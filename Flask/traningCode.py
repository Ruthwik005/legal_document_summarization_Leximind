from google.colab import drive
import os
import glob
import torch
import torch.nn as nn
import torch.optim as optim
import pdfplumber
import random
import math
from transformers import AutoTokenizer
from torch.utils.data import DataLoader, Dataset
from torch.amp import autocast, GradScaler
from huggingface_hub import login

# ✅ Authenticate Hugging Face and set device
drive.mount('/content/drive')
login(token="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")
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ✅ Load Tokenizer
tokenizer = AutoTokenizer.from_pretrained("t5-small")
vocab_size = tokenizer.vocab_size

# ✅ Checkpoint directory
checkpoint_dir = "/content/drive/MyDrive/legal_summarization_checkpoints_6"
os.makedirs(checkpoint_dir, exist_ok=True)

def manage_checkpoints():
    files = sorted(glob.glob(os.path.join(checkpoint_dir, "transformer_epoch_*_1.pt")), key=os.path.getctime)
    if len(files) > 2:
        for old in files[:-2]:
            os.remove(old)

# 🔧 Data Augmentation Functions

def random_deletion(text, p=0.1):
    words = text.split()
    if len(words) == 0:
        return text
    # drop each word with probability p
    new_words = [w for w in words if random.random() > p]
    if len(new_words) == 0:
        new_words = [random.choice(words)]
    return " ".join(new_words)


def random_swap(text, n_swaps=1):
    words = text.split()
    for _ in range(n_swaps):
        if len(words) < 2:
            break
        i, j = random.sample(range(len(words)), 2)
        words[i], words[j] = words[j], words[i]
    return " ".join(words)


def augment_text(text):
    # randomly choose one augmentation
    r = random.random()
    if r < 0.3:
        return random_deletion(text, p=0.1)
    elif r < 0.6:
        return random_swap(text, n_swaps=1)
    else:
        return text

# 🔧 Text Loading and Splitting

def extract_text_from_pdf(pdf_path, chunk_size=512):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    words = text.split()
    return [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]


def load_texts_from_folder(folder_path, chunk_size=512, augment=False):
    texts = []
    for fname in sorted(os.listdir(folder_path)):
        path = os.path.join(folder_path, fname)
        if path.endswith('.pdf'):
            chunks = extract_text_from_pdf(path, chunk_size)
        else:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
        texts.extend(chunks)
        if augment:
            texts.extend([augment_text(c) for c in chunks])
    return texts

# 🔧 Dataset

class LegalDataset(Dataset):
    def init(self, texts, summaries, tokenizer, input_max_len=512, summary_max_len=900):
        self.texts = texts[:3000]
        self.summaries = summaries[:len(self.texts)]
        self.tokenizer = tokenizer
        self.input_max_len = input_max_len
        self.summary_max_len = summary_max_len

    def len(self):
        return len(self.texts)

    def getitem(self, idx):
        text = self.texts[idx]
        summary = self.summaries[idx]
        inputs = self.tokenizer(text, padding="max_length", truncation=True,
                                 max_length=self.input_max_len, return_tensors="pt")
        targets = self.tokenizer(summary, padding="max_length", truncation=True,
                                  max_length=self.summary_max_len, return_tensors="pt")
        return {
            'input_ids': inputs['input_ids'].squeeze(0),
            'attention_mask': inputs['attention_mask'].squeeze(0),
            'labels': targets['input_ids'].squeeze(0)
        }

# 🔧 Model Definition

class PositionalEncoding(nn.Module):
    def init(self, d_model, dropout=0.1, max_len=1024):
        super().init()
        self.dropout = nn.Dropout(p=dropout)
        position = torch.arange(0, max_len).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2) * (-math.log(10000.0) / d_model))
        pe = torch.zeros(1, max_len, d_model)
        pe[0, :, 0::2] = torch.sin(position * div_term)
        pe[0, :, 1::2] = torch.cos(position * div_term)
        self.register_buffer('pe', pe)

    def forward(self, x):
        x = x + self.pe[:, :x.size(1)]
        return self.dropout(x)

class CustomTransformer(nn.Module):
    def init(self, vocab_size, d_model=512, nhead=8,
                 num_encoder_layers=6, num_decoder_layers=6,
                 dim_feedforward=2048, dropout=0.1):
        super().init()
        self.embedding = nn.Embedding(vocab_size, d_model)
        self.pos_encoder = PositionalEncoding(d_model, dropout)
        self.transformer = nn.Transformer(d_model=d_model, nhead=nhead,
                                          num_encoder_layers=num_encoder_layers,
                                          num_decoder_layers=num_decoder_layers,
                                          dim_feedforward=dim_feedforward,
                                          dropout=dropout, batch_first=True)
        self.fc_out = nn.Linear(d_model, vocab_size)

    def forward(self, src, tgt):
        src = self.pos_encoder(self.embedding(src))
        tgt = self.pos_encoder(self.embedding(tgt))
        output = self.transformer(src, tgt)
        return self.fc_out(output)

# 🔧 Training Loop

def train_model(model, dataloader, optimizer, criterion, device, epochs=5):
    model.train().to(device)
    scaler = GradScaler()
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=3)

    # Resume or scratch
    checkpoints = sorted(glob.glob(os.path.join(checkpoint_dir, "transformer_epoch_*_1.pt")),
                         key=os.path.getctime)
    if checkpoints:
        ckpt = checkpoints[-1]
        model.load_state_dict(torch.load(ckpt, map_location=device))
        print(f"Resumed from {ckpt}")
    else:
        print("Training from scratch...")

    for epoch in range(epochs):
        total_loss, correct, total = 0, 0, 0
        for step, batch in enumerate(dataloader):
            optimizer.zero_grad()
            input_ids = batch['input_ids'].to(device)
            labels = batch['labels'].to(device)
            decoder_input = labels[:, :-1]
            target = labels[:, 1:]

            with autocast(device_type="cuda" if device.type=="cuda" else "cpu"):
                outputs = model(input_ids, decoder_input)
                loss = criterion(outputs.view(-1, outputs.size(-1)), target.reshape(-1))

            scaler.scale(loss).backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            scaler.step(optimizer)
            scaler.update()
            scheduler.step(loss)

            total_loss += loss.item()
            preds = outputs.argmax(dim=-1)
            correct += (preds == target).sum().item()
            total += target.numel()

        acc = correct / total * 100
        avg_loss = total_loss / len(dataloader)
        ckpt_path = os.path.join(checkpoint_dir, f"transformer_epoch_{epoch+1}_1.pt")
        torch.save(model.state_dict(), ckpt_path)
        manage_checkpoints()
        print(f"Epoch {epoch+1}: Loss={avg_loss:.4f}, Acc={acc:.2f}%")

# ✅ Main Execution

if name == "main":
    train_texts = load_texts_from_folder(
        "/content/drive/MyDrive/dataset/IN-Abs/train-data/judgement",
        chunk_size=512, augment=True
    )
    train_summaries = load_texts_from_folder(
        "/content/drive/MyDrive/dataset/IN-Abs/train-data/summary",
        chunk_size=512, augment=False
    )
    dataset = LegalDataset(train_texts, train_summaries, tokenizer)
    dataloader = DataLoader(dataset, batch_size=4, shuffle=True)

    model = CustomTransformer(vocab_size).to(device)
    optimizer = optim.Adam(model.parameters(), lr=1e-4)
    criterion = nn.CrossEntropyLoss(ignore_index=tokenizer.pad_token_id)

    train_model(model, dataloader, optimizer, criterion, device, epochs=20)
