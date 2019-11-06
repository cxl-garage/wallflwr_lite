
Deer_Binary:
    - trained only on a few hundred (200-300) images of deer gathered by Will and Mia, source unclear. 
    - Manually labelled. 
    - Trained for highest performance (sacrificing latency)

Deer_Binary_v2:
    - trained with 2500 images, including the prior. Datasets used include:
        - caltech cameratraps
        - missouri cameratraps
        - openimages
    - trained for best tradeoff, aka half latency half performance

Deer_Binary_v3:
    - trained with 4000 images. NOT including same images/labels from the first set, composed of:
        - caltech cameratraps
        - missouri cameratraps
        - openimages
        - Will and Mia's data (~1500 images) + megadetector
    - trained for fastest predictions, sacrificing performance.
