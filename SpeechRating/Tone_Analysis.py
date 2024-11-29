# Import required packages
import os
import librosa
import librosa.display
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset

# Plotting audio file
def plot_audio_waveform(file_path):
    data, sampling_rate = librosa.load(file_path)
    plt.figure(figsize=(15, 5))
    librosa.display.waveshow(data, sr=sampling_rate)
    plt.title("Audio Waveform")
    plt.show()

# Extract features using librosa
def extract_features(file_list, label_fetcher):
    df = pd.DataFrame(columns=['feature', 'emotion'])
    for index, file_path in enumerate(file_list):
        try:
            X, sample_rate = librosa.load(file_path, res_type='kaiser_fast', duration=3, sr=22050 * 2, offset=0.5)
            mfccs = np.mean(librosa.feature.mfcc(y=X, sr=sample_rate, n_mfcc=13), axis=0)
            emotion = label_fetcher(file_path)  # Assume label_fetcher is a function to get the emotion label
            df.loc[index] = [mfccs, emotion]
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
    return df

# Preprocess the data
def preprocess_data(df):
    feature_df = pd.DataFrame(df['feature'].values.tolist())
    labelled_df = pd.concat([feature_df, df['emotion']], axis=1)
    cleaned_df = labelled_df.dropna()
    shuffled_df = cleaned_df.sample(frac=1).reset_index(drop=True)

    # Remove unwanted emotions
    unwanted_emotions = [
        'male_neutral', 'male_disgusted', 'male_surprised',
        'female_neutral', 'female_disgusted', 'female_surprised'
    ]
    filtered_df = shuffled_df.loc[~shuffled_df['emotion'].isin(unwanted_emotions)]

    # Split data
    X = filtered_df.drop('emotion', axis=1)
    y = filtered_df['emotion']
    return train_test_split(X, y, test_size=0.2, random_state=42, shuffle=True)

# PyTorch Dataset class
class EmotionDataset(Dataset):
    def __init__(self, X, y):
        self.X = torch.tensor(X.values, dtype=torch.float32)
        self.y = torch.tensor(y.values, dtype=torch.long)

    def __len__(self):
        return len(self.y)

    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]

# Encode labels
def encode_labels(y_train, y_test):
    lb = LabelEncoder()
    y_train = lb.fit_transform(y_train)
    y_test = lb.transform(y_test)
    return y_train, y_test, lb

# PyTorch Model
class EmotionCNN(nn.Module):
    def __init__(self, input_shape, num_classes):
        super(EmotionCNN, self).__init__()
        self.conv1 = nn.Conv1d(in_channels=input_shape[0], out_channels=256, kernel_size=5, padding=2)
        self.conv2 = nn.Conv1d(256, 128, kernel_size=5, padding=2)
        self.conv3 = nn.Conv1d(128, 128, kernel_size=5, padding=2)
        self.dropout = nn.Dropout(0.5)
        self.pool = nn.MaxPool1d(kernel_size=8)
        self.flatten = nn.Flatten()
        self.fc = nn.Linear(128 * (input_shape[1] // 8), num_classes)

    def forward(self, x):
        x = torch.relu(self.conv1(x))
        x = torch.relu(self.conv2(x))
        x = self.dropout(self.pool(x))
        x = torch.relu(self.conv3(x))
        x = self.flatten(x)
        x = self.fc(x)
        return x

# Main process
def main(train_data_path):
    # Fetch all audio files
    file_list = []
    for path, _, files in os.walk(train_data_path):
        for name in files:
            file_list.append(os.path.join(path, name))

    # Extract features and emotions
    df = extract_features(file_list, fetch_label.FetchLabel().get_emotion)  # Replace with your label fetcher logic

    # Preprocess data
    X_train, X_test, y_train, y_test = preprocess_data(df)

    # Encode labels
    y_train, y_test, label_encoder = encode_labels(y_train, y_test)

    # PyTorch DataLoader
    train_dataset = EmotionDataset(X_train, pd.Series(y_train))
    test_dataset = EmotionDataset(X_test, pd.Series(y_test))

    train_loader = DataLoader(train_dataset, batch_size=512, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=512, shuffle=False)

    # Model setup
    input_shape = (1, X_train.shape[1])
    model = EmotionCNN(input_shape=(1, X_train.shape[1]), num_classes=len(label_encoder.classes_))
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    # Training loop
    model.train()
    for epoch in range(50):
        total_loss = 0
        for batch_X, batch_y in train_loader:
            batch_X = batch_X.unsqueeze(1)  # Add channel dimension
            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        print(f"Epoch {epoch + 1}, Loss: {total_loss:.4f}")

    # Save model
    model_path = os.path.join('saved_models', 'Emotion_Voice_Detection_Model.pt')
    os.makedirs('saved_models', exist_ok=True)
    torch.save(model.state_dict(), model_path)
    print(f"Model saved to {model_path}")

    return model, label_encoder

# Example usage
if __name__ == "__main__":
    train_data_path = "path/to/train/data"  # Replace with your training data path
    model, label_encoder = main(train_data_path)
