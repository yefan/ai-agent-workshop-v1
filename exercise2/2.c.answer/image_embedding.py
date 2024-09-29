import math
from sentence_transformers import SentenceTransformer, util
import os.path
import pickle
from scipy import spatial
from PIL import Image
import faiss
import numpy as np
from pathlib import Path
import base64
import openai


from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
import matplotlib

image_pkl_path = 'clip_embedding.pkl'

# Add description, and tutorial type of comments
class image_embedding_store:
    def __init__(self, dataset_dir) -> None:
        self.dataset_dir = dataset_dir
        self.model = SentenceTransformer('clip-ViT-B-32')
        self.embedding_dict = self.update_imgage_embedding()

        self.id_to_name = {}
        self.embedding_list = []
        next_id = 0
        for file_name, embedding in self.embedding_dict.items():
            self.id_to_name[next_id] = file_name
            self.embedding_list.append(embedding)
            next_id = next_id + 1

        self.animal_labels = ["cat", "dog", "bird", "fish", "horse"]
        self.animal_label_embedding = self.model.encode(self.animal_labels)

    def update_imgage_embedding(self):
        embedding_dict = {}

        if os.path.isfile(f"{self.dataset_dir}/{image_pkl_path}"):
            with open(f"{self.dataset_dir}/{image_pkl_path}", 'rb') as file:
                embedding_dict = pickle.load(file)

        embedding_dict_updated = False
        file_in_dataset = []
        for path in Path(self.dataset_dir).rglob('*.[jp][pn]g'):
            filename = os.fsdecode(path)
            file_in_dataset.append(filename)
            if filename in embedding_dict:
                continue
            embedding_dict_updated = True
            print(f"Generating embedding for {filename}")

            embedding_dict[filename] = self.model.encode(Image.open(f"{filename}"))
        all_files = list(embedding_dict.keys())
        files_not_in_dataset = [x for x in all_files if x not in file_in_dataset]
        for file in files_not_in_dataset:
            del embedding_dict[file]
            embedding_dict_updated = True

        print(f"Number of images in dataset: {len(embedding_dict)}")

        if embedding_dict_updated:
            with open(f"{self.dataset_dir}/{image_pkl_path}", "wb") as file:
                pickle.dump(embedding_dict, file)

        return embedding_dict

    def get_all_files(self):
        return list(self.embedding_dict.keys())

    def find_top_k_similar_images_by_text(self, description, k=3):
        text_embedding = self.model.encode(description)
        distances = []
        for name, vec in self.embedding_dict.items():
            similarity = spatial.distance.euclidean(text_embedding, vec)
            distances.append((name, similarity))

        # Sort by similarity in descending order
        distances.sort(key=lambda x: x[1])

        # Get the top k similar images
        top_k_images = [name for name, _ in distances[:k]]
        return top_k_images
    
    def find_top_k_similar_images_by_image(self, image_path, k=3):
        image_embedding = self.model.encode(Image.open(f"{self.dataset_dir}/{image_path}"))
        distances = []
        for name, vec in self.embedding_dict.items():
            similarity = spatial.distance.euclidean(image_embedding, vec)
            distances.append((name, similarity))

        # Sort by similarity in descending order
        distances.sort(key=lambda x: x[1])

        # Get the top k similar images
        top_k_images = [name for name, _ in distances[:k]]
        return top_k_images
    
    def categorize_animal_image(self, image_path):
        image_embedding = self.model.encode(Image.open(f"{self.dataset_dir}/{image_path}"))
        distances = [[i, spatial.distance.euclidean(image_embedding, vec)] for i, vec in enumerate(self.animal_label_embedding)]
        sorted_distances = sorted(distances, key=lambda x: x[1])
        return self.animal_labels[sorted_distances[0][0]]

# Test stub for the different search algorithms
if __name__ == "__main__":
    dataset_dir = 'dataset'
    # Example usage of the image embedding functionalities
    img_store = image_embedding_store(dataset_dir)  # Assuming ImageEmbedding is the class name

    query = "a cat reading a book"

    closest_image = img_store.find_top_k_similar_images_by_text(query, k=1)
    print(f"Closest image: {closest_image}")

    closest_image = img_store.find_top_k_similar_images_by_image("cat_studying_b.png", k=1)
    print(f"Closest image: {closest_image}")

    animal = img_store.categorize_animal_image("cat_a.png")
    print(f"Animal: {animal}")
