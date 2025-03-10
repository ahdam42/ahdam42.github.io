from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import io
import time


VECTOR_SIZE = 100


def load_vectors(fname):
    fin = io.open(fname, 'r', encoding='utf-8', newline='\n', errors='ignore')
    n, d = map(int, fin.readline().split())
    data = {}
    for line in fin:
        tokens = line.rstrip().split(' ')
        data[tokens[0]] = map(float, tokens[1:])
    return data


def get_vector(text, model):
    # Усреднение векторов слов в тексте
    vectors = [model[word] for word in text if word in model]

    if not vectors:
        return np.zeros(model.vector_size)
    return np.mean(vectors, axis=0)


if __name__ == "__main__":
    start_time = time.time()

    text1 = "A ConvNeXt for the 2020s The article presents a new convolutional neural network (ConvNet) architecture, dubbed ConvNeXt, which challenges the dominance of Vision Transformers in various computer vision tasks. It explores how to modernize a standard ResNet towards the design of hierarchical vision Transformer while maintaining simplicity as a ConvNet. The authors start with a standard ResNet-50 model and gradually modernize it by incorporating several design choices from Vision Transformers, including:1. Improved training techniques (like AdamW optimizer, Mixup, Cutmix, etc.).2. Macro design changes: adjusting stage compute ratio, using a patchify stem cell.3. ResNeXt-ifying the network with grouped convolutions and expanding width.4. Inverted bottleneck design.5. Large kernel sizes for depthwise convolution.6. Micro-level design modifications: replacing ReLU with GELU, reducing activation functions, reducing normalization layers, substituting BatchNorm with Layer Normalization, and separating downsampling layers. ConvNeXt models outperform Swin Transformers on several benchmarks while maintaining the simplicity and efficiency of standard ConvNets. On ImageNet classification, ConvNeXt-T achieves 81.6% top-1 accuracy and ConvNeXt-B achieves 82.0% with fewer parameters and FLOPs than Swin models. On COCO detection, ConvNeXt-B outperforms Swin-B by 3.5 AP with a faster inference speed (174 ms vs. 296 ms). On ADE20K segmentation, ConvNeXt-T achieves 44.8 mIOU and ConvNeXt-B achieves 45.7 mIOU, outperforming Swin models by 0.3-0.5 mIOU. The article does not provide a detailed ablation study to quantify the impact of each design choice individually.- It does not discuss potential limitations or biases in their training procedure or data augmentation techniques used. ConvNeXt challenges the recent dominance of Vision Transformers and demonstrates that ConvNets can still achieve state-of-the-art performance with appropriate architectural and training choices. The exploration process provides valuable insights into how design decisions from Vision Transformers can be adapted for ConvNets, potentially leading to further advancements in both fields."
    text2 = "MMDetection: Open MMLab Detection Toolbox and Benchmark Object detection and instance segmentation, a fundamental task in computer vision. Various object detection and instance segmentation methods, components, and hyperparameters. A comprehensive toolbox (MMDetection) built using PyTorch to support popular detection frameworks, modular design for easy customization, and high-efficiency GPU operations. The toolbox is benchmarked on the COCO 2017 dataset with different methods, backbones, and settings. MMDetection supports more methods (over 20) and features than other popular codebases (Detectron, maskrcnn-benchmark, SimpleDet), including recent ones like RetinaNet, GHM, FCOS, FSAF, Grid R-CNN, Mask Scoring R-CNN, Double-Head R-CNN, Hybrid Task Cascade, etc. Benchmarking results show competitive or superior performance and speed for various methods with different backbones (ResNet-50/101, ResNeXt101-64x4d).- Comparison with other codebases demonstrates similar or lower memory usage and faster inference speeds for Mask R-CNN and RetinaNet. Mixed precision training reduces GPU memory and speeds up training without significant performance loss. Multi-node scalability shows nearly linear acceleration for distributed training. The results may vary depending on the hardware setup, implementation details, and specific datasets used (e.g., COCO 2017). Some compared codebases are under development, and their results might be outdated or tested on different hardware. The study focuses mainly on performance and speed; other aspects like power consumption and model size are not considered. MMDetection serves as a high-quality codebase and unified benchmark for object detection and instance segmentation research, enabling fair comparisons between methods and settings. It facilitates the reimplementation of existing methods and development of new detectors by providing a flexible toolkit with various supported frameworks, components, and modules. The toolbox can be applied to other computer vision tasks that share similar training pipelines, such as image classification and semantic segmentation."
    text3 = "Bees may be solitary or may live in various types of communities. Eusociality appears to have originated from at least three independent origins in halictid bees. The most advanced of these are species with eusocial colonies; these are characterized by cooperative brood care and a division of labour into reproductive and non-reproductive adults, plus overlapping generations. This division of labour creates specialized groups within eusocial societies which are called castes. In some species, groups of cohabiting females may be sisters, and if there is a division of labour within the group, they are considered semisocial. The group is called eusocial if, in addition, the group consists of a mother (the queen) and her daughters (workers). When the castes are purely behavioural alternatives, with no morphological differentiation other than size, the system is considered primitively eusocial, as in many paper wasps; when the castes are morphologically discrete, the system is considered highly eusocial."
    text4 = "Abstract—In this paper, we propose a novel method for monocular depth estimation in dynamic scenes. We first explore the arbitrariness of object’s movement trajectory in dynamic scenes theoretically. To overcome the arbitrariness, we use assume that points move along a straight line over short distances and then summarize it as a triangular constraint loss in two dimensional Euclidean space. This triangular loss function is used as part of our proposed pixel movement prediction network, PMPNet, to estimate a dense depth map from a single input image. To overcome the depth inconsistency problem around the edges, we propose a deformable support window module that learns features from different shapes of objects, making depth value more accurate around edge area. The proposed model is trained and tested on two outdoor datasets - KITTI and Make3D, as well as an indoor dataset - NYU Depth V2. The quantitative and qualitative results reported on these datasets demonstrate the success of our proposed model when compared against other approaches. Ablation study results on the KITTI dataset also validate the effectiveness of the proposed pixel movement prediction module as well as the deformable support window module."
    text5 = "Monocular depth estimation, which plays a crucial role in understanding 3D scene geometry, is an ill-posed problem. Recent methods have gained significant improvement by exploring image-level information and hierarchical features from deep convolutional neural networks (DCNNs). These methods model depth estimation as a regression problem and train the regression networks by minimizing mean squared error, which suffers from slow convergence and unsatisfactory local solutions. Besides, existing depth estimation networks employ repeated spatial pooling operations, resulting in undesirable low-resolution feature maps. To obtain high-resolution depth maps, skipconnections or multi-layer deconvolution networks are required, which complicates network training and consumes much more computations. To eliminate or at least largely reduce these problems, we introduce a spacing-increasing discretization (SID) strategy to discretize depth and recast depth network learning as an ordinal regression problem. By training the network using an ordinary regression loss, our method achieves much higher accuracy and faster convergence in synch. Furthermore, we adopt a multi-scale network structure which avoids unnecessary spatial pooling and captures multi-scale information in parallel."

    # query = "In probability theory, the joint probability distribution is the probability distribution of all possible pairs of outputs of two random variables that are defined on the same probability space. The joint distribution can just as well be considered for any given number of random variables."
    # query = "Bees feed on nectar and pollen, the former primarily as an energy source and the latter primarily for protein and other nutrients. Most pollen is used as food for their larvae. Vertebrate predators of bees include primates and birds such as bee-eaters; insect predators include beewolves and dragonflies."
    query = "Semantic Segmentation is a computer vision task in which the goal is to categorize each pixel in an image into a class or object. The goal is to produce a dense pixel-wise segmentation map of an image, where each pixel is assigned to a specific class or object. Some example benchmarks for this task are Cityscapes, PASCAL VOC and ADE20K. Models are usually evaluated with the Mean Intersection-Over-Union (Mean IoU) and Pixel Accuracy metrics."
    query = "About ConvNeXts a new convolutional neural network (ConvNet) architecture"

    tokenized_text1 = text1.lower().split()
    tokenized_text2 = text2.lower().split()
    tokenized_text3 = text3.lower().split()
    tokenized_text4 = text4.lower().split()
    tokenized_text5 = text5.lower().split()
    tokenized_query = query.lower().split()

    # corpus = [tokenized_text1, tokenized_text2, tokenized_text3]
    # model_w2v = Word2Vec(sentences=corpus, vector_size=VECTOR_SIZE, window=20, min_count=1, workers=4)

    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

    vector1 = model.encode(text1)
    vector2 = model.encode(text2)
    vector3 = model.encode(text3)
    vector4 = model.encode(text4)
    vector5 = model.encode(text5)
    vectorq = model.encode(query)

    print(f"Косинусное сходство: {cosine_similarity([vector1], [vectorq])[0][0]}")
    print(f"Косинусное сходство: {cosine_similarity([vector2], [vectorq])[0][0]}")
    print(f"Косинусное сходство: {cosine_similarity([vector3], [vectorq])[0][0]}")
    print(f"Косинусное сходство: {cosine_similarity([vector1], [vector2])[0][0]}")
    print(f"Косинусное сходство: {cosine_similarity([vector1], [vector3])[0][0]}")
    print(f"Косинусное сходство: {cosine_similarity([vector1], [vector4])[0][0]}")
    print(f"Косинусное сходство: {cosine_similarity([vector4], [vector5])[0][0]}")
    print(f"Косинусное сходство: {cosine_similarity([vector1], [vector5])[0][0]}")

    print("Time: ", time.time() - start_time)


'''
import numpy as np
import faiss

# Генерация случайных векторов для примера
np.random.seed(1234)
vectors = np.random.random((1000, 128)).astype('float32')

# Создание индекса FAISS
index = faiss.IndexFlatL2(128)  # 128 - размерность векторов

# Добавление векторов в индекс
index.add(vectors)

# Поиск 5 наиболее похожих векторов для заданного вектора
query_vector = np.random.random((1, 128)).astype('float32')
k = 5
distances, indices = index.search(query_vector, k)

print("Индексы наиболее похожих векторов:", indices)
print("Расстояния до наиболее похожих векторов:", distances)

print(indices[0][0])
print(len(vectors[indices[0][0]]))
'''
