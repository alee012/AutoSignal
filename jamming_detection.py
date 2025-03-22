import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.datasets import make_classification

# Define file path for storing data
DATA_FILE = "jamming_data.csv"

# Step 1: Load Data from CSV or Generate New Data

print("\n-------------------------------------------------------")

if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
    print("\nData loaded from jamming_data.csv\n")
else:
    print("\n⚠️ No existing data found. Generating new dataset...\n")
    X, y = make_classification(n_samples=1000, n_features=3, 
                               n_informative=2, n_redundant=0, 
                               n_clusters_per_class=1  )

    df = pd.DataFrame(X, columns=['Signal_Strength', 'Noise_Level', 'Frequency_Variability'])
    df['Jamming_Detected'] = y  # 0 = Normal, 1 = Jammed

    # Save to CSV
    df.to_csv(DATA_FILE, index=False)
    print(f"New dataset generated and saved to {DATA_FILE}")

# Step 2: Split Data into Training and Testing Sets
X = df[['Signal_Strength', 'Noise_Level', 'Frequency_Variability']]
y = df['Jamming_Detected']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2  )

# Step 3: Normalize Features
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

# Step 4: Train an SVM Model
print("Training SVM model...\n")
svm_model = SVC(kernel='rbf', C=1.0, gamma='scale', random_state=42)
svm_model.fit(X_train, y_train)
print("Model training complete")

# Step 5: Make Predictions
y_pred = svm_model.predict(X_test)

# Step 6: Evaluate Performance

print("\n-------------------------------------------------------")

accuracy = accuracy_score(y_test, y_pred)
print(f'\n Accuracy: {accuracy:.2f}')

print("\n Classification Report:")
print(classification_report(y_test, y_pred))

print("\n Confusion Matrix:")
print(confusion_matrix(y_test, y_pred))

# Step 7: Visualizing Results with PCA
from sklearn.decomposition import PCA

pca = PCA(n_components=2)
X_train_pca = pca.fit_transform(X_train)
X_test_pca = pca.transform(X_test)

svm_model.fit(X_train_pca, y_train)
y_pred_pca = svm_model.predict(X_test_pca)

plt.figure(figsize=(8,6))
plt.scatter(X_test_pca[:,0], X_test_pca[:,1], c=y_pred_pca, cmap='coolwarm', alpha=0.7)
plt.title('SVM Decision Boundaries (PCA-reduced)')
plt.xlabel('PCA Component 1')
plt.ylabel('PCA Component 2')
plt.savefig('svm_decision_boundaries.png')  # Save the plot
plt.show()
