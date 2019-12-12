# -*- coding: utf-8 -*-
#
# Animal Detection Network (Andenet)
# Author: Peter Ersts (ersts@amnh.org)
#
# --------------------------------------------------------------------------
#
# This file is part of Animal Detection Network (Andenet).
#
# Andenet is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Andenet is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.
#
# --------------------------------------------------------------------------
import os
import io
import random
import hashlib
import numpy as np
import tensorflow as tf
from PIL import Image
from PyQt5 import QtCore


def int64_feature(value):
    return tf.train.Feature(int64_list=tf.train.Int64List(value=[value]))


def int64_list_feature(value):
    return tf.train.Feature(int64_list=tf.train.Int64List(value=value))


def bytes_feature(value):
    return tf.train.Feature(bytes_list=tf.train.BytesList(value=[value]))


def bytes_list_feature(value):
    return tf.train.Feature(bytes_list=tf.train.BytesList(value=value))


def float_list_feature(value):
    return tf.train.Feature(float_list=tf.train.FloatList(value=value))


class Exporter(QtCore.QThread):
    """Export annotated image examples into the Tensorflow TFRecord format."""

    progress = QtCore.pyqtSignal(int)
    exported = QtCore.pyqtSignal()

    def __init__(self,
                 directory,
                 images,
                 label_map,
                 validation_split,
                 masks={},
                 strip_metadata=False):
        """
        Class init function.

        Args:
            directory (str): Destination directory
            image_data (File): Image and Annotation List
            labels_map (dict): Class/label names
            validation_split (float): Percent to use for validation
            masks (dict): Binary arrays for masking metadata
            strip_metadata (bool): Flag for stripping metadata
        """
        QtCore.QThread.__init__(self)
        self.directory = directory
        self.images = images
        self.label_map = label_map
        self.train_size = int((1.0 - validation_split) * len(self.images))

        self.masks = masks
        self.strip_metadata = strip_metadata

        for mask in masks:
            m = np.array(masks[mask], dtype='uint8')
            self.masks[mask] = np.dstack((m, m, m))

        self.labels = []
        for label in label_map:
            if label_map[label].lower() != 'exclude':
                if label_map[label] == '':
                    label_map[label] = label
                self.labels.append(label_map[label])

    def run(self):
        """
        The starting point for the thread.

        After creating and instance of the class, calling start() will call
        this function which exports all of the annotaiton examples to disk.
        """
        random.shuffle(self.images)

        counter = 0
        train_writer = tf.python_io.TFRecordWriter(
            os.path.join(self.directory, 'training.record'))
        validation_writer = tf.python_io.TFRecordWriter(
            os.path.join(self.directory, 'validation.record'))
        for example in self.images:
            file_name = os.path.join(
                example['directory'], example['file_name'])

            with tf.gfile.GFile(file_name, 'rb') as fid:
                encoded_jpg = fid.read()
            encoded_jpg_io = io.BytesIO(encoded_jpg)
            image = Image.open(encoded_jpg_io)
            if image.format != 'JPEG':
                raise ValueError('Image format not JPEG')
            key = hashlib.sha256(encoded_jpg).hexdigest()
            size = image.size  # PIL (width, height)
            image.close()

            xmins = []
            ymins = []
            xmaxs = []
            ymaxs = []
            classes = []
            classes_text = []
            occluded = []
            truncated = []
            difficult = []
            for annotation in example['annotations']:
                label = self.label_map[annotation['label']]
                xmins.append(annotation['bbox']['xmin'])
                ymins.append(annotation['bbox']['ymin'])
                xmaxs.append(annotation['bbox']['xmax'])
                ymaxs.append(annotation['bbox']['ymax'])
                classes_text.append(label.encode('utf8'))
                classes.append(self.labels.index(label) + 1)
                if annotation['occluded'] == 'Y':
                    occluded.append(1)
                else:
                    occluded.append(0)

                if annotation['truncated'] == 'Y':
                    truncated.append(1)
                else:
                    truncated.append(0)

                if annotation['difficult'] == 'Y':
                    difficult.append(1)
                else:
                    difficult.append(0)

            feature_dict = {
                'image/height': int64_feature(size[1]),
                'image/width': int64_feature(size[0]),
                'image/filename': bytes_feature(file_name.encode('utf8')),
                'image/source_id': bytes_feature(file_name.encode('utf8')),
                'image/key/sha256': bytes_feature(key.encode('utf8')),
                'image/encoded': bytes_feature(encoded_jpg),
                'image/format': bytes_feature('jpeg'.encode('utf8')),
                'image/object/bbox/xmin': float_list_feature(xmins),
                'image/object/bbox/xmax': float_list_feature(xmaxs),
                'image/object/bbox/ymin': float_list_feature(ymins),
                'image/object/bbox/ymax': float_list_feature(ymaxs),
                'image/object/class/text': bytes_list_feature(classes_text),
                'image/object/class/label': int64_list_feature(classes),
                'image/object/difficult': int64_list_feature(difficult),
                'image/object/truncated': int64_list_feature(truncated),
                'image/object/occluded': int64_list_feature(occluded),
            }
            tf_example = tf.train.Example(
                features=tf.train.Features(feature=feature_dict))
            if counter <= self.train_size:
                train_writer.write(tf_example.SerializeToString())
            else:
                validation_writer.write(tf_example.SerializeToString())
            counter += 1
            self.progress.emit(counter)
        train_writer.close()
        validation_writer.close()
        file = open(os.path.join(self.directory, 'label_map.pbtxt'), 'w')
        for counter in range(len(self.labels)):
            template = "item {{\n name: \"{}\"\n id: {}\n}}\n"
            file.write(template.format(self.labels[counter], counter + 1))
        file.close()
        self.exported.emit()
