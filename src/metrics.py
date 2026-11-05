"""Dice and two-class mean IoU for binary liver masks."""
import numpy as np


def confusion(prediction, ground_truth):
    """Return integer TP, FP, FN, TN counts; masks must have equal shapes."""
    p, g = np.asarray(prediction, bool), np.asarray(ground_truth, bool)
    if p.shape != g.shape:
        raise ValueError('Mask shape mismatch')
    tp = int(np.count_nonzero(p & g))
    predicted = int(np.count_nonzero(p))
    actual = int(np.count_nonzero(g))
    return tp, predicted-tp, actual-tp, int(p.size-predicted-actual+tp)


def from_confusion(tp, fp, fn, tn, empty_value=1.0):
    """Return fractional scores; an empty class in both masks scores 1."""
    dice_denominator = 2*tp + fp + fn
    liver_denominator = tp + fp + fn
    background_denominator = tn + fp + fn
    dice = 2*tp/dice_denominator if dice_denominator else empty_value
    liver = tp/liver_denominator if liver_denominator else empty_value
    background = tn/background_denominator if background_denominator else empty_value
    return dict(dice=dice, miou=(liver+background)/2, iou_liver=liver, iou_bg=background)


def scores(prediction, ground_truth, empty_value=1.0):
    return from_confusion(*confusion(prediction, ground_truth), empty_value)
