from numpy import concatenate, array

from neupy.utils import format_data
from neupy.core.properties import IntProperty
from neupy.algorithms.learning import SupervisedLearningMixin
from neupy.algorithms.base import BaseNetwork


__all__ = ('CMAC',)


class CMAC(SupervisedLearningMixin, BaseNetwork):
    """
    CMAC Network based on memory.

    Notes
    -----
    - Network always use Mean Absolute Error (MAE).
    - Network works for multi dimensional target values.

    Parameters
    ----------
    quantization : int
        Network transforms every input to discrete value.
        Quantization value contol number of total possible
        categories after quantization, defaults to ``10``.

    associative_unit_size : int
        Number of associative blocks in memory, defaults to ``2``.

    {BaseNetwork.Parameters}

    Attributes
    ----------
    weight : dict
        Network's weight that contains memorized patterns.

    Methods
    -------
    {BaseSkeleton.predict}

    {SupervisedLearningMixin.train}

    {BaseSkeleton.fit}

    Examples
    --------
    >>> import numpy as np
    >>> from neupy.algorithms import CMAC
    >>>
    >>> train_space = np.linspace(0, 2 * np.pi, 100)
    >>> test_space = np.linspace(np.pi, 2 * np.pi, 50)
    >>>
    >>> input_train = np.reshape(train_space, (100, 1))
    >>> input_test = np.reshape(test_space, (50, 1))
    >>>
    >>> target_train = np.sin(input_train)
    >>> target_test = np.sin(input_test)
    >>>
    >>> cmac = CMAC(
    ...     quantization=100,
    ...     associative_unit_size=32,
    ...     step=0.2,
    ... )
    ...
    >>> cmac.train(input_train, target_train, epochs=100)
    >>>
    >>> predicted_test = cmac.predict(input_test)
    >>> cmac.error(target_test, predicted_test)
    0.0023639417543036569
    """
    quantization = IntProperty(default=10, minval=1)
    associative_unit_size = IntProperty(default=2, minval=2)

    def __init__(self, **options):
        self.weight = {}
        super(CMAC, self).__init__(**options)

    def predict(self, input_data):
        input_data = format_data(input_data)

        get_memory_coords = self.get_memory_coords
        get_result_by_coords = self.get_result_by_coords
        predicted = []

        for input_sample in self.quantize(input_data):
            coords = get_memory_coords(input_sample)
            predicted.append(get_result_by_coords(coords))

        return array(predicted)

    def get_result_by_coords(self, coords):
        return sum(
            self.weight.setdefault(coord, 0) for coord in coords
        ) / self.associative_unit_size

    def get_memory_coords(self, quantized_value):
        assoc_unit_size = self.associative_unit_size

        for i in range(assoc_unit_size):
            point = ((quantized_value + i) / assoc_unit_size).astype(int)
            yield tuple(concatenate([point, [i]]))

    def quantize(self, input_data):
        return (input_data * self.quantization).astype(int)

    def train_epoch(self, input_train, target_train):
        get_memory_coords = self.get_memory_coords
        get_result_by_coords = self.get_result_by_coords
        weight = self.weight
        step = self.step

        n_samples = input_train.shape[0]
        quantized_input = self.quantize(input_train)
        errors = 0

        for input_sample, target_sample in zip(quantized_input, target_train):
            coords = list(get_memory_coords(input_sample))
            predicted = get_result_by_coords(coords)

            error = target_sample - predicted
            for coord in coords:
                weight[coord] += step * error

            errors += abs(error)

        return errors / n_samples
