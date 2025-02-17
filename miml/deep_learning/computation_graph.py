from org.deeplearning4j.nn.conf import NeuralNetConfiguration
from org.deeplearning4j.nn.graph import ComputationGraph
from org.deeplearning4j.optimize.listeners import ScoreIterationListener
from org.nd4j.linalg.api.ndarray import INDArray
from org.nd4j.linalg.indexing import NDArrayIndex
from org.nd4j.evaluation.classification import Evaluation
from org.nd4j.linalg.util import FeatureUtil
from org.meteothink.miml.nd4j import Nd4jUtil
import mipylib.numeric as np
import network_util

class ComputationGraph(object):
    '''
    Computation graph Neural Network.


    '''

    def __init__(self, seed=123, weight_init=None, learning_rate=None, optimizer=None, updater=None,
                 bias_init=None, l1=None, l2=None, mini_batch=None, layers=None, **kwargs):
        self.seed = seed
        self.weight_init = weight_init
        self.learning_rate = learning_rate
        self.optimizer = optimizer
        self.updater = updater
        self.bias_init = bias_init
        self.l1 = l1
        self.l2 = l2
        self.mini_batch = mini_batch
        self.inputs = None
        self.layers = layers
        self.outputs = None
        self._model = None
        self.score_iter = None

    def add_inputs(self, inputs):
        '''
        Add a list of strings telling the network what layers to use as input layers

        :param inputs: (*List of string*) A list of strings as input layers.
        '''
        self.inputs = inputs

    def add_layer(self, name, layer, inputs):
        '''
        Add a layer

        :param name: (*string*) Layer name.
        :param layer: (*Layer*) The layer.
        :param inputs: (*list of string*) A list of strings defined previously to feed this layer as inputs
        '''
        if self.layers is None:
            self.layers = []
        self.layers.append([name, layer, inputs])

    def set_outputs(self, outputs):
        '''
        Set output layers

        :param outputs: (*list of string*) A list of strings telling the network what layers to use as
            output layers.
        '''
        self.outputs = outputs

    def compile(self, score_iter=10):
        '''
        Build the network.

        :param score_iter: (*int*) Number of parameter updates for printing score
        '''
        confb = NeuralNetConfiguration.Builder() \
            .seed(self.seed)
        if not self.learning_rate is None:
            confb.learningRate(self.learning_rate)
        if not self.optimizer is None:
            confb.optimizationAlgo(self.optimizer)
        if not self.updater is None:
            confb.updater(self.updater)
        if not self.weight_init is None:
            confb.weightInit(self.weight_init)
        if not self.bias_init is None:
            confb.biasInit(self.bias_init)
        if not self.l1 is None:
            confb.l1(self.l1)
        if not self.l2 is None:
            confb.l2(self.l2)
        if not self.mini_batch is None:
            confb.miniBatch(self.mini_batch)
        confb = confb.graphBuilder()
        confb.addInputs(self.inputs)
        for layer in self.layers:
            confb.addLayer(layer[0], layer[1]._layer, layer[2])
        confb.setOutputs(self.outputs)
        conf = confb.build()
        self._model = ComputationGraph(conf)
        self._model.init()
        self.score_iter = score_iter
        self._model.setListeners(ScoreIterationListener(self.score_iter))

    def fit(self, x, y, epochs=1, batchsize=None):
        """
        Learn from input data and labels.

        :param x: (*array*) Training samples. 2D array.
        :param y: (*array*) Training labels in [0, c), where c is the number of classes.
        :param epochs: (*int*) Number of fit epochs.
        :param batchsize: (*int*) Batch size of training data for each fit process.
        """
        n = len(x)
        x = Nd4jUtil.toNDArray(x._array)
        if y.ndim == 1:
            #y = y.tojarray('int')
            y = Nd4jUtil.toNDMatrix(y._array, self.nout)
        else:
            y = Nd4jUtil.toNDArray(y._array)
        stride = epochs / 10;
        ppi = 0
        for i in range(epochs):
            if epochs >= 10:
                if i == ppi or i == epochs - 1:
                    print 'Epoch %i' % (i + 1)
                    ppi += stride
            if batchsize is None:
                self._model.fit(x, y)
            else:
                si = 0
                while si < n:
                    ei = si + batchsize if si + batchsize <= n else n
                    xx = x.get(NDArrayIndex.interval(si, ei))
                    if isinstance(y, INDArray):
                        yy = y.get(NDArrayIndex.interval(si, ei))
                    else:
                        yy = y[si:ei]
                    self._model.fit(xx, yy)
                    si += batchsize

    def predict(self, x):
        """
        Predict the class labels for the provided data

        Parameters
        ----------
        X : array-like, shape (n_query, n_features), \
                or (n_query, n_indexed) if metric == 'precomputed'
            Test samples.

        Returns
        -------
        y : array of shape [n_samples] or [n_samples, n_outputs]
            Class labels for each data sample.
        """
        x = Nd4jUtil.toNDArray(x._array)
        r = self._model.output(x)
        r = Nd4jUtil.toArray(r)
        return np.array(r)

    def eval(self, x, y, batchsize=None):
        """
        Evaluation from input data and labels.

        :param x: (*array*) Training samples. 2D array.
        :param y: (*array*) Training labels in [0, c), where c is the number of classes.
        :param batchsize: (*int*) Batch size of training data for each fit process.
        """
        _eval = Evaluation(self.nout)
        n = len(x)
        x = Nd4jUtil.toNDArray(x._array)
        if batchsize is None:
            y_pred = self._model.output(x)
            y = FeatureUtil.toOutcomeMatrix(y.tojarray('int'), self.nout)
            _eval.eval(y, y_pred)
        else:
            si = 0
            while si < n:
                ei = si + batchsize if si + batchsize <= n else n
                xx = x.get(NDArrayIndex.interval(si, ei))
                yy = y[si:ei]
                yy = FeatureUtil.toOutcomeMatrix(yy.tojarray('int'), self.nout)
                y_pred = self._model.output(xx)
                _eval.eval(yy, y_pred)
                si += batchsize

        return _eval.stats()