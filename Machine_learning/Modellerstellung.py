from sklearn.linear_model import LinearRegression
import pickle

# Einfaches Modell trainieren
model = LinearRegression()
X = [[1], [2], [3], [4]]
y = [2, 4, 6, 8]
model.fit(X, y)

# Als .pkl Datei speichern
with open('test_model.pkl', 'wb') as f:
    pickle.dump(model, f)