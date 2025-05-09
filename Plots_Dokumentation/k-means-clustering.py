import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.lines import Line2D
import matplotlib.gridspec as gridspec

# Für Reproduzierbarkeit
np.random.seed(42)

# Farbpalette
COLORS = ['#3498db', '#e74c3c', '#2ecc71', '#9b59b6', '#f39c12']
CENTROIDS_COLOR = '#34495e'
BACKGROUND = '#f5f5f5'


# Datensatz mit 3 klar getrennten Clustern erstellen
def create_cluster_data():
    # Cluster 1 - unten links
    cluster1 = np.random.randn(20, 2) * 0.5 + np.array([-3.0, -3.0])

    # Cluster 2 - oben
    cluster2 = np.random.randn(20, 2) * 0.5 + np.array([0.0, 4.0])

    # Cluster 3 - unten rechts
    cluster3 = np.random.randn(20, 2) * 0.5 + np.array([3.0, -3.0])

    # Zusammenfügen der Daten
    X = np.vstack([cluster1, cluster2, cluster3])

    return X


# Einfache K-Means Implementierung mit Geschichte
class KMeans:
    def __init__(self, n_clusters=3, max_iters=10, random_state=None):
        self.n_clusters = n_clusters
        self.max_iters = max_iters
        self.random_state = random_state
        self.centroids = None
        self.history = []

    def fit(self, X):
        if self.random_state is not None:
            np.random.seed(self.random_state)

        # Zufällige Punkte als initiale Zentroiden auswählen
        indices = np.random.choice(X.shape[0], self.n_clusters, replace=False)
        self.centroids = X[indices]

        # Initialen Zustand speichern
        initial_labels = self.assign_clusters(X)
        self.history.append({
            'iteration': 0,
            'centroids': self.centroids.copy(),
            'labels': initial_labels
        })

        # Hauptschleife des Algorithmus
        for iteration in range(1, self.max_iters + 1):
            # Zuordnung der Punkte zu Clustern
            labels = self.assign_clusters(X)

            # Aktualisierung der Zentroiden
            new_centroids = np.zeros_like(self.centroids)
            for i in range(self.n_clusters):
                if np.sum(labels == i) > 0:  # Wenn Cluster nicht leer ist
                    new_centroids[i] = np.mean(X[labels == i], axis=0)
                else:
                    # Falls Cluster leer, behalte alten Zentroid
                    new_centroids[i] = self.centroids[i]

            # Zustand speichern
            self.history.append({
                'iteration': iteration,
                'centroids': new_centroids.copy(),
                'labels': labels
            })

            # Überprüfen auf Konvergenz
            if np.allclose(new_centroids, self.centroids):
                break

            self.centroids = new_centroids

        return self

    def assign_clusters(self, X):
        """Jedem Punkt den nächsten Zentroid zuweisen"""
        distances = np.sqrt(((X[:, np.newaxis, :] - self.centroids[np.newaxis, :, :]) ** 2).sum(axis=2))
        return np.argmin(distances, axis=1)


# Hauptfunktion für die Visualisierung
def visualize_kmeans_schema():
    # Daten erstellen
    X = create_cluster_data()

    # K-Means ausführen
    k_means = KMeans(n_clusters=3, random_state=42)
    k_means.fit(X)

    # Figure erstellen
    fig = plt.figure(figsize=(12, 10), facecolor='white')
    gs = gridspec.GridSpec(2, 2, figure=fig, wspace=0.25, hspace=0.3)

    # Achsenlimits bestimmen
    x_min, x_max = X[:, 0].min() - 1, X[:, 0].max() + 1
    y_min, y_max = X[:, 1].min() - 1, X[:, 1].max() + 1

    # Ausgewählte Iterationen für die Visualisierung
    history_len = len(k_means.history)
    iterations_to_show = [0]  # Start mit Initialisierung

    # Weitere Iterationen hinzufügen
    if history_len > 2:
        # Wir wollen eine frühe, eine mittlere und die letzte Iteration
        iterations_to_show.append(1)  # Erste echte Iteration
        iterations_to_show.append(min(2, history_len - 1))  # Mittlere oder zweite Iteration
        iterations_to_show.append(history_len - 1)  # Letzte Iteration
    else:
        # Bei weniger als 3 Iterationen, alle anzeigen
        iterations_to_show = list(range(history_len))

    # Für jede ausgewählte Iteration einen Plot erstellen
    for i, iter_idx in enumerate(iterations_to_show[:4]):
        ax = fig.add_subplot(gs[i])

        # Zustand aus Historie laden
        state = k_means.history[iter_idx]

        # Titel setzen
        if iter_idx == 0:
            ax.set_title("Initialisierung", fontsize=14, fontweight='bold')
        else:
            ax.set_title(f"Iteration {iter_idx}", fontsize=14, fontweight='bold')

        # Hintergrund setzen
        ax.set_facecolor(BACKGROUND)

        # Punkte zeichnen, eingefärbt nach Clusterzugehörigkeit
        for cluster_idx in range(k_means.n_clusters):
            cluster_points = X[state['labels'] == cluster_idx]
            ax.scatter(
                cluster_points[:, 0],
                cluster_points[:, 1],
                color=COLORS[cluster_idx],
                s=80,
                edgecolor='black',
                linewidth=1,
                alpha=0.8
            )

        # Zentroiden zeichnen
        for j, centroid in enumerate(state['centroids']):
            # Zentroid als Stern
            ax.scatter(
                centroid[0],
                centroid[1],
                marker='*',
                color=CENTROIDS_COLOR,
                s=300,
                edgecolor='black',
                linewidth=1.5,
                zorder=10,
                label=f'Zentroid {j + 1}' if i == 0 else ""
            )

            # Kreis um den Zentroid für Sichtbarkeit
            circle = Circle(
                (centroid[0], centroid[1]),
                0.3,
                fill=False,
                color=COLORS[j],
                linestyle='--',
                linewidth=1.5,
                alpha=0.8
            )
            ax.add_patch(circle)

            # Verbindungslinien zu zugehörigen Punkten im ersten und letzten Plot
            if i in [0, 3]:  # Nur Initialisierung und letzte Iteration
                for point_idx, point in enumerate(X):
                    if state['labels'][point_idx] == j:
                        ax.plot(
                            [centroid[0], point[0]],
                            [centroid[1], point[1]],
                            color=COLORS[j],
                            linestyle='-',
                            linewidth=0.5,
                            alpha=0.3
                        )

        # Achsenlimits und Raster
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        ax.grid(True, linestyle='--', alpha=0.5)

        # Achsenbeschriftungen
        ax.set_xlabel("Merkmal 1", fontsize=12)
        ax.set_ylabel("Merkmal 2", fontsize=12)

        # Clusterstatistik anzeigen
        unique, counts = np.unique(state['labels'], return_counts=True)
        stats_text = "Clustergröße:\n"
        for u, c in zip(unique, counts):
            stats_text += f"Cluster {u + 1}: {c} Punkte\n"

        ax.text(
            0.05, 0.95,
            stats_text,
            transform=ax.transAxes,
            fontsize=10,
            va='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8)
        )

    # Legende erstellen
    handles = []
    labels = []

    # Clusterfarben für Legende
    for i in range(k_means.n_clusters):
        handles.append(
            Line2D([0], [0], marker='o', color='w', markerfacecolor=COLORS[i], markersize=10, label=f'Cluster {i + 1}')
        )
        labels.append(f'Cluster {i + 1}')

    # Zentroid für Legende
    handles.append(
        Line2D([0], [0], marker='*', color='w', markerfacecolor=CENTROIDS_COLOR, markersize=15, label='Zentroid')
    )
    labels.append('Zentroide')

    # Legende im ersten Plot platzieren
    plt.figlegend(
        handles,
        labels,
        loc='lower center',
        ncol=4,
        fontsize=12,
        bbox_to_anchor=(0.5, 0.02)
    )

    plt.suptitle('K-Means Clustering Schema', fontsize=18, fontweight='bold', y=0.98)


    plt.tight_layout(rect=[0, 0.05, 1, 0.92])

    # Speichern und Anzeigen
    plt.savefig('kmeans_schema.png', dpi=300, bbox_inches='tight')
    plt.show()

    # Statistik ausgeben
    print(f"Anzahl der Iterationen bis zur Konvergenz: {len(k_means.history)}")

    return k_means


# Ausführen
if __name__ == "__main__":
    kmeans_model = visualize_kmeans_schema()