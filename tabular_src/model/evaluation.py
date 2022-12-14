import numpy as np
import pandas as pd
import json
from copy import deepcopy
from sklearn.metrics import (f1_score, accuracy_score, confusion_matrix, precision_score, recall_score,
                             multilabel_confusion_matrix, log_loss, roc_auc_score, classification_report)

from ..utils import get_logger

logger = get_logger(__name__)


class HelperMetricCalculation(object):

    def __init__(self, y_true, y_pred, y_pred_proba):
        self.y_true = y_true
        self.y_pred = y_pred
        self.y_pred_proba = y_pred_proba

    def score(self, fun, top_x=None, **kwargs):
        """"""
        if top_x is not None:
            if self.y_pred_proba is not None and sum(self.y_pred_proba) != 0:
                df = pd.DataFrame({'y_true': self.y_true, 'y_pred': self.y_pred, 'y_pred_proba': self.y_pred_proba})
                df = df.sort_values(by=['y_pred_proba'], ascending=False, ignore_index=True)
                df_length = df.shape[0]
            else:
                return None
            if 0 < top_x <= 1:
                num_top_p = int(df_length * top_x)
                df_slice = df.head(num_top_p)
                return fun(np.asarray(df_slice['y_true']), np.asarray(df_slice['y_pred']), **kwargs)
            else:
                logger.info("top_x should be between 0 and 1 or a positive integer.")
                return None
        else:
            return fun(self.y_true, self.y_pred, **kwargs)


class EvaluateClassification(object):
    """"""
    def __init__(self, estimator, labels, pred_proba, prob_threshold, multi_label=False):
        assert isinstance(labels, (pd.Series, np.ndarray))
        assert isinstance(pred_proba, (pd.Series, np.ndarray))
        if isinstance(labels, pd.Series):
            labels = np.asarray(labels)
        if isinstance(pred_proba, pd.Series):
            pred_proba = np.asarray(pred_proba)

        if not multi_label:
            logger.info('Evaluation is set for binary-classification')
            self.labels = labels
            self.pred_proba = pred_proba
            self.preds = np.where(self.pred_proba < prob_threshold, 0, 1)
            self.estimator = estimator

            s = HelperMetricCalculation(self.labels, self.preds, self.pred_proba)
            self.accuracy_score = accuracy_score(labels.flatten(), self.preds.flatten())
            self.f1_score = f1_score(labels.flatten(), self.preds.flatten(), average='macro')
            self.recall = s.score(recall_score)
            self.recall_top_1 = s.score(recall_score, top_x=0.01)
            self.recall_top_5 = s.score(recall_score, top_x=0.05)
            self.recall_top_10 = s.score(recall_score, top_x=0.1)
            self.precision = s.score(precision_score)
            self.precision_top_1 = s.score(precision_score, top_x=0.01)
            self.precision_top_5 = s.score(precision_score, top_x=0.05)
            self.precision_top_10 = s.score(precision_score, top_x=0.1)
            self.confusion_matrix = confusion_matrix(labels, self.preds)
        else:
            logger.info('Evaluation is set for multi-classification')
            # TODO 2: Implement for multiclass
            # self.confusion_matrix = multilabel_confusion_matrix(labels, self.preds)
        self.classification_report = classification_report(labels, self.preds, output_dict=True)

    def show(self):
        """"""
        logger.info('Accuracy: {}'.format(self.accuracy_score))
        logger.info('F1 score: {}'.format(self.f1_score))
        logger.info('Confusion matrix:\n{}'.format(self.confusion_matrix))
        logger.info('Classification report:\n{}'.format(self.classification_report))
        logger.info('recall score: {}'.format(self.recall))
        logger.info('recall in top 1 percentile {}'.format(self.recall_top_1))
        logger.info('precision score: {}'.format(self.precision))
        logger.info('precision score in top 1 percentile {}'.format(self.precision_top_1))
        print(classification_report(self.labels, self.preds))

    def to_dict(self):
        """"""
        res = {
            'accuracy': self.accuracy_score,
            'f1_score': self.f1_score,
            'classification_report': self.classification_report,
            'confusion_matrix': self.confusion_matrix,
            'recall_score': self.recall,
            'recall_top1': self.recall_top_1,
            'recall_top5': self.recall_top_5,
            'recall_top10': self.recall_top_10,
            'precision_score': self.precision,
            'precision_top1': self.precision_top_1,
            'precision_top5': self.precision_top_5,
            'precision_top10': self.precision_top_10,
        }
        return res

    def to_json(self):
        """"""
        dic = self.to_dict()
        res = deepcopy(dic)
        res['confusion_matrix'] = res['confusion_matrix'].tolist()
        return res

    def save(self, filepath: str = None, plot: bool = False, plot_path: str = None):
        """"""
        res = self.to_json()
        with open(filepath, 'w') as fp:
            json.dump(res, fp)
            logger.info('Evaluation result saved to: {}'.format(filepath))
        if not plot:
            logger.info('Not generating evaluation plots')
        else:
            logger.info('Saving plots at {}'.format(plot_path))
            self.plot(path=plot_path)

    def plot(self, path: str = None):
        """"""
        from pycaret.classification import plot_model
        plot_model(estimator=self.estimator, plot='learning', save=path, use_train_data=False)
        plot_model(estimator=self.estimator, plot='confusion_matrix', save=path, use_train_data=False)
        plot_model(estimator=self.estimator, plot='pr', save=path, use_train_data=False)
        plot_model(estimator=self.estimator, plot='lift', save=path, use_train_data=False)
        plot_model(estimator=self.estimator, plot='gain', save=path, use_train_data=False)
        plot_model(estimator=self.estimator, plot='auc', save=path, use_train_data=False)


class EvaluateRegression(object):
    # TODO 1: Implement for regression

    def __init__(self, labels, preds, multi_label=False):
        assert isinstance(labels, (pd.Series, np.ndarray))
        assert isinstance(preds, (pd.Series, np.ndarray))
        if isinstance(labels, pd.Series):
            labels = np.asarray(labels)
        if isinstance(preds, pd.Series):
            preds = np.asarray(preds)

        self.labels = labels
        self.preds = preds

        self.accuracy_score = accuracy_score(labels.flatten(), preds.flatten())
        self.f1_score = f1_score(labels.flatten(), preds.flatten(), average='macro')
        if not multi_label:
            self.confusion_matrix = confusion_matrix(labels, preds)
        else:
            self.confusion_matrix = multilabel_confusion_matrix(labels, preds)
        self.classification_report = classification_report(labels, preds, output_dict=True)

    def show(self):
        logger.info('Accuracy: {}'.format(self.accuracy_score))
        logger.info('F1 score: {}'.format(self.f1_score))
        logger.info('Confusion matrix:\n{}'.format(self.confusion_matrix))
        logger.info('Classification report:\n{}'.format(self.classification_report))
        print(classification_report(self.labels, self.preds))

    def to_dict(self):
        res = {
            'accuracy': self.accuracy_score,
            'f1_score': self.f1_score,
            'classification_report': self.classification_report,
            'confusion_matrix': self.confusion_matrix
        }
        return res

    def to_json(self):
        dic = self.to_dict()
        res = deepcopy(dic)
        res['confusion_matrix'] = res['confusion_matrix'].tolist()
        return res

    def save(self, filepath):
        res = self.to_json()
        with open(filepath, 'w') as fp:
            json.dump(res, fp)
            logger.info('Evaluation result saved to: {}'.format(filepath))
