import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch

# Farbdefinition
BLUE = '#3498db'  # Positive Klasse
RED = '#e74c3c'  # Negative Klasse
GREEN = '#2ecc71'  # Entscheidungsgrenze
PURPLE = '#9b59b6'  # Gewichtsvektor

# Für Reproduzierbarkeit
np.random.seed(42)


# Datensatz mit genau 4 Epochen bis zur Konvergenz
def create_example_data():
    # Positive Klasse
    positive_class = np.array([
        [3.0, 3.5],
        [4.0, 2.5],
        [5.0, 4.0]
    ])

    # Negative Klasse - sorgfältig platziert für 4 Epochen
    negative_class = np.array([
        [1.0, 1.0],
        [2.0, 0.0],
        [0.0, 2.0]
    ])

    # Zusammenfügen der Daten
    X = np.vstack([positive_class, negative_class])
    y = np.array([1, 1, 1, -1, -1, -1])

    return X, y


# Einfacher Perzeptron-Algorithmus
class Perceptron:
    def __init__(self):
        self.weights = None
        self.bias = None
        self.history = []

    def fit(self, X, y, max_epochs=10):
        n_samples, n_features = X.shape

        # Initialgewichte für stabile 4 Epochen
        self.weights = np.array([0.5, 0.5])
        self.bias = -0.5

        # Initial state speichern
        self.history.append((self.weights.copy(), self.bias, self._get_misclassified(X, y)))

        # Training über mehrere Epochen
        for epoch in range(1, max_epochs + 1):
            any_misclassified = False

            # Feste Reihenfolge für Reproduzierbarkeit
            for idx in range(len(X)):
                x_i = X[idx]
                # Vorhersage berechnen
                y_pred = 1 if np.dot(x_i, self.weights) + self.bias > 0 else -1

                # Gewichte aktualisieren, wenn falsch klassifiziert
                if y_pred != y[idx]:
                    self.weights += y[idx] * x_i
                    self.bias += y[idx]
                    any_misclassified = True

            # Zustand am Ende der Epoche speichern
            self.history.append((self.weights.copy(), self.bias, self._get_misclassified(X, y)))

            # Abbruch, wenn alle korrekt klassifiziert
            if not any_misclassified:
                break

    def _get_misclassified(self, X, y):
        """Gibt Indizes falsch klassifizierter Punkte zurück"""
        predictions = [1 if np.dot(x, self.weights) + self.bias > 0 else -1 for x in X]
        return [i for i, (p, yi) in enumerate(zip(predictions, y)) if p != yi]


# Funktion zum Zeichnen der Entscheidungsgrenze und des Gewichtsvektors
def plot_decision_boundary_and_vector(ax, weights, bias, xlim, ylim):
    # Entscheidungsgrenze zeichnen
    x = np.linspace(xlim[0], xlim[1], 100)
    y = (-weights[0] * x - bias) / weights[1] if abs(weights[1]) > 1e-10 else np.ones_like(x) * float('inf')

    # Nur zeichnen, wenn die Linie im sichtbaren Bereich liegt
    mask = (y >= ylim[0]) & (y <= ylim[1])
    if any(mask):
        ax.plot(x[mask], y[mask], color=GREEN, linewidth=2)

    # Gewichtsvektor zeichnen - Vektor skalieren für bessere Sichtbarkeit
    vector_length = np.sqrt(weights[0] ** 2 + weights[1] ** 2)
    if vector_length > 0:  # Wenn Vektor nicht Null ist
        scale = 1.5 / vector_length  # Skalierungsfaktor für einheitliche Länge
        arrow = FancyArrowPatch(
            (0, 0),
            (weights[0] * scale, weights[1] * scale),
            arrowstyle='->',
            linewidth=2,
            color=PURPLE,
            mutation_scale=15
        )
        ax.add_patch(arrow)

        # Orthogonalität demonstrieren mit gestrichelter Linie
        if abs(weights[1]) > 1e-10:
            # Naher Punkt auf der Entscheidungsgrenze zum Ursprung berechnen
            t = -bias / (weights[0] ** 2 + weights[1] ** 2)
            near_point = (t * weights[0], t * weights[1])

            # Nur zeichnen, wenn der Punkt im sichtbaren Bereich liegt
            if (xlim[0] <= near_point[0] <= xlim[1]) and (ylim[0] <= near_point[1] <= ylim[1]):
                ax.plot([0, near_point[0]], [0, near_point[1]], 'k--', linewidth=1, alpha=0.6)


# Hauptfunktion für die Visualisierung
def plot_perceptron_schema():
    # Daten erstellen
    X, y = create_example_data()

    # Perzeptron trainieren
    model = Perceptron()
    model.fit(X, y, max_epochs=10)

    # Wir erwarten genau 4 Epochen (Initialisierung + 3 Updates)
    # Epochen 0, 1, 2, 3 sollten im history-Array enthalten sein

    # 2x2 Subplot erstellen
    fig, axes = plt.subplots(2, 2, figsize=(10, 8))
    axes = axes.flatten()

    # Achsenlimits bestimmen
    x_min, x_max = X[:, 0].min() - 1, X[:, 0].max() + 1
    y_min, y_max = X[:, 1].min() - 1, X[:, 1].max() + 1

    # Positive und negative Indizes
    pos_idx = np.where(y == 1)[0]
    neg_idx = np.where(y == -1)[0]

    # Für jede Epoche einen Plot erstellen
    for i in range(min(4, len(model.history))):
        ax = axes[i]

        # Zustand aus History laden
        weights, bias, misclassified = model.history[i]

        # Plot-Titel
        if i == 0:
            ax.set_title(f"Initialisierung", fontsize=12)
        else:
            ax.set_title(f"Epoche {i}", fontsize=12)

        # Zeichne jeden Punkt
        for idx in range(len(X)):
            # Bestimme Farbe und Marker basierend auf Klasse und Klassifikation
            color = BLUE if y[idx] == 1 else RED

            # Zeichne den Datenpunkt
            ax.scatter(X[idx, 0], X[idx, 1], color=color, s=100, edgecolor='black')

            # Füge kleine Textbeschriftung hinzu
            ax.text(X[idx, 0] + 0.1, X[idx, 1] + 0.1, f"{idx + 1}", fontsize=9)

        # Entscheidungsgrenze und Gewichtsvektor zeichnen
        plot_decision_boundary_and_vector(ax, weights, bias, (x_min, x_max), (y_min, y_max))

        # Koordinatensystem
        ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        ax.axvline(x=0, color='black', linestyle='-', alpha=0.3)

        # Achsenlimits und Raster
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        ax.grid(True, linestyle='--', alpha=0.5)

        # Beschriftungen
        ax.set_xlabel('Merkmal 1')
        ax.set_ylabel('Merkmal 2')

        # Anzahl falsch klassifizierter Punkte
        n_misclassified = len(misclassified)
        ax.text(0.05, 0.95, f"Falsch klassifiziert: {n_misclassified}",
                transform=ax.transAxes, fontsize=9, va='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    # Legende im ersten Plot
    handles = [
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=BLUE, markersize=10, label='Positive Klasse'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=RED, markersize=10, label='Negative Klasse'),
        plt.Line2D([0], [0], marker='s', color='w', markerfacecolor='gray', markersize=10,
                   label='Falsch klassifiziert'),
        plt.Line2D([0], [0], color=GREEN, linewidth=2, label='Entscheidungsgrenze'),
        plt.Line2D([0], [0], color=PURPLE, marker='>', markersize=8, linewidth=2, label='Gewichtsvektor')
    ]
    axes[0].legend(handles=handles, loc='upper right', fontsize=8)

    plt.suptitle('Perzeptron-Algorithmus: Konvergenz in 4 Epochen', fontsize=16)
    plt.tight_layout()
    plt.subplots_adjust(top=0.9)

    # Speichern und Anzeigen
    plt.savefig('perzeptron_schema_4epochen.png', dpi=300)
    plt.show()

    # Anzahl der Epochen ausgeben
    print(f"Anzahl der Epochen bis zur Konvergenz: {len(model.history)}")

    return model


# Ausführen
if __name__ == "__main__":
    model = plot_perceptron_schema()