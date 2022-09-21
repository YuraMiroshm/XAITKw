from xaitk_saliency import ImageSimilaritySaliencyMapGenerator
from xaitk_saliency.utils.masking import weight_regions_by_scalar

import numpy as np
from sklearn.preprocessing import minmax_scale
import scipy


class SimilarityScoring (ImageSimilaritySaliencyMapGenerator):
    """
    This saliency implementation transforms proximity in feature
    space into saliency heatmaps. This should
    require a sequence of feature vectors of the query and
    reference image, a number of feature vectors as predicted
    on perturbed images, as well as the masks of the reference image
    perturbations (as would be output from a
    `PerturbImage` implementation.

    The perturbation masks used by the following implementation are
    expected to be of type integer. Masks containing values of type
    float are rounded to the nearest value and binarized
    with value 1 replacing values greater than or equal to half of
    the maximum value in mask after rounding while 0 replaces the rest.

    param proximity_metric: The type of comparision metric to be used
        to determine proximity in feature space. The following
        metrics are currently supported.

        ‘braycurtis’, ‘canberra’, ‘chebyshev’, ‘cityblock’, ‘correlation’,
        ‘cosine’, ‘dice’, ‘euclidean’, ‘hamming’, ‘jaccard’, ‘jensenshannon’,
        ‘kulsinski’, ‘mahalanobis’, ‘matching’, ‘minkowski’, ‘rogerstanimoto’,
        ‘russellrao’, ‘seuclidean’, ‘sokalmichener’, ‘sokalsneath’,
        ‘sqeuclidean’, ‘wminkowski’, ‘yule’.
    """

    def __init__(
        self,
        proximity_metric: str ='euclidean'
    ):
        self.proximity_metric: str = proximity_metric

    def generate(
        self,
        ref_descr_1: np.ndarray,
        ref_descr_2: np.ndarray,
        perturbed_descrs: np.ndarray,
        perturbed_masks: np.ndarray,
    ) -> np.ndarray:

        # Computing original proximity between image1 and image2 feature vectors.
        original_proximity = scipy.spatial.distance.cdist(
            ref_descr_1.reshape(1, -1),
            ref_descr_2.reshape(1, -1),
            metric=self.proximity_metric
        )

        # Computing proximity between original image1 and perturbed image2 feature vectors.
        perturbed_proximity = scipy.spatial.distance.cdist(
            ref_descr_1.reshape(1, -1),
            perturbed_descrs,
            metric=self.proximity_metric
        )[0]

        if len(perturbed_proximity) != len(perturbed_masks):
            raise ValueError("Number of perturbation masks and respective",
                             "confidence lengths do not match.")

        # Iterating through each distance and compare it with
        # its perturbed twin
        diff_abs = perturbed_proximity - original_proximity

        diff = np.transpose(np.clip(diff_abs, 0, None))
        # Weighting perturbed regions with respective difference in confidence
        sal = weight_regions_by_scalar(diff, perturbed_masks)

        # Converting nan values to zero.
        sal = np.nan_to_num(sal)
        # Normalize final saliency map in range [0, 1]
        sal = minmax_scale(sal.ravel(), feature_range=(0, 1)).reshape(sal.shape)

        return sal

    def get_config(self) -> dict:
        return {
            "proximity_metric": self.proximity_metric,
        }
