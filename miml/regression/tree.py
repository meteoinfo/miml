# -*- coding: utf-8 -*-

from smile.regression import RegressionTree as JRegressionTree
from smile.data.formula import Formula
from org.meteothink.miml.util import SmileUtil

import mipylib.numeric as np
from .regressor import Regressor

class RegressionTree(Regressor):
    """
    Decision tree for regression.

    A decision tree can be learned by splitting the training set into subsets based on an attribute
    value test. This process is repeated on each derived subset in a recursive manner called
    recursive partitioning. The recursion is completed when the subset at a node all has the same
    value of the target variable, or when splitting no longer adds value to the predictions.

    :param max_depth: (*int*) the maximum depth of the tree.
    :param max_nodes: (*int*) The maximum number of leaf nodes in the tree.
    :param node_size: (*int*) the minimum size of leaf nodes.
    """
    
    def __init__(self,  max_depth=20, max_nodes=0, node_size=5):
        super(RegressionTree, self).__init__()

        self.max_depth = max_depth
        self.max_nodes = max_nodes
        self.node_size = node_size
    
    def fit(self, x, y):
        """
        Learn from input data and labels.
        
        :param x: (*array*) Training samples. 2D array.
        :param y: (*array*) Training labels in [0, c), where c is the number of classes.
        """
        df = SmileUtil.toDataFrame(x.asarray(), y.asarray())
        formula = Formula.lhs("class")
        if self.max_nodes == 0:
            self.max_nodes = df.size() / 5
        self._model = JRegressionTree.fit(formula, df, self.max_depth, self.max_nodes, self.node_size)

    def predict(self, x):
        x = np.atleast_2d(x)
        y = np.zeros(len(x))
        df = SmileUtil.toDataFrame(x.asarray(), y.asarray())
        r = self._model.predict(df)
        return np.array(r)

    @property
    def feature_importances_(self):
        """Return the feature importances.

        The importance of a feature is computed as the (normalized) total
        reduction of the criterion brought by that feature.
        It is also known as the Gini importance.

        Returns
        -------
        feature_importances_ : array, shape = [n_features]
        """
        if self._model is None:
            return None
        else:
            importances = np.array(self._model.importance())
            normalizer = np.sum(importances)
            if normalizer > 0.0:
                importances /= normalizer
            return importances
        
##################################################