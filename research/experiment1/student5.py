from model import Model

from sklearn.utils import shuffle

import numpy as np
import tensorflow as tf


class Student5(Model):
  def __init__(self, name):
    print("Student5::__init__")
    super().__init__(name)

    # placeholders for input and output variables in the dataset (x = features, y = labels)

    # x = 28 x 28 pixels from images
    # y = one hot vector where 1 denotes the correct label
    self.x = tf.placeholder(tf.float32, shape=[None, 784])
    self.y_ = tf.placeholder(tf.float32, shape = [None, 10])

    # reshape the input to a 4d tensor (-1 since we don't know how many images we have)
    # the second and third dimension is the srze of the image
    # and the last dimension repressents the number of color channels
    self.x_image = tf.reshape(self.x, [-1, 28, 28, 1])

    # The first convolutional layer
    self.W_conv1 = Model.weight_variable([5, 5, 1, 2])
    self.b_conv1 = Model.bias_variable([2])

    # convolve the image with a relu activation function
    self.h_conv1 = tf.nn.relu(Model.conv2d(self.x_image, self.W_conv1) + self.b_conv1)

    # The first convolutional max pool layer
    self.W_conv_max_pool_1 = Model.weight_variable([2, 2, 2, 2])
    self.b_conv_max_pool_1 = Model.bias_variable([2])
    # add max_pooling layer based on a convolutional layer
    self.h_pool1 = tf.nn.relu(Model.conv2d_stride2x2(self.h_conv1, self.W_conv_max_pool_1) +
        self.b_conv_max_pool_1)

    # create the fully connected layer
    self.W_fc1 = Model.weight_variable([14 * 14 * 2, 10])
    self.b_fc1 = Model.bias_variable([10])

    # reshape the pooling layer to be flat
    self.h_pool1_flat = tf.reshape(self.h_pool1, [-1, 14 * 14 * 2])
    self.y_conv = tf.matmul(self.h_pool1_flat, self.W_fc1) + self.b_fc1

    # learning rate
    self.learning_rate = 0.0001

    # train and evaluate
    self.cross_entropy = tf.reduce_mean(
        tf.nn.softmax_cross_entropy_with_logits(labels = self.y_, logits = self.y_conv))
    self.train_step = tf.train.AdamOptimizer(self.learning_rate).minimize(self.cross_entropy)
    self.correct_prediction = tf.equal(tf.argmax(self.y_conv, 1), tf.argmax(self.y_, 1))
    self.accuracy = tf.reduce_mean(tf.cast(self.correct_prediction, tf.float32))

  def train(self, mnist):
    print("Student5::train")

    n_epochs = 50
    batch_size = 50
    n_batches = len(mnist.train.images) // batch_size

    losses = []
    accs = []
    test_accs = []

    with Model.Session() as sess:
      sess.run(tf.global_variables_initializer())
      for epoch in range(n_epochs):
          x_shuffle, y_shuffle \
                  = shuffle(mnist.train.images, mnist.train.labels)
          print("Starting training opoch %d" % epoch)
          for i in range(n_batches):
              start = i * batch_size
              end = start + batch_size
              batch_x, batch_y \
                      = x_shuffle[start:end], y_shuffle[start:end]
              sess.run(self.train_step, feed_dict = {
                  self.x: batch_x,
                  self.y_: batch_y })
          x_shuffle, y_shuffle \
                  = shuffle(mnist.train.images, mnist.train.labels)
          batch_x, batch_y \
                  = x_shuffle[0:250], y_shuffle[0:250]
          train_loss = sess.run(self.cross_entropy, feed_dict = {
              self.x: batch_x,
              self.y_: batch_y })
          train_accuracy = sess.run(self.accuracy, feed_dict = {
              self.x: batch_x,
              self.y_: batch_y })
          test_accuracy = sess.run(self.accuracy, feed_dict = {
              self.x: mnist.test.images,
              self.y_: mnist.test.labels })
          print("Epoch : %i, Loss : %f, Accuracy: %f, Test accuracy: %f" % (
                  epoch + 1, train_loss, train_accuracy, test_accuracy))
          losses.append(train_loss)
          accs.append(train_accuracy)
          test_accs.append(test_accuracy)

          super().append_to_csv("train_loss", epoch, train_loss)
          super().append_to_csv("train_accuracy", epoch, train_accuracy)
          super().append_to_csv("test_accuracy", epoch, test_accuracy)

    return (losses, accs, test_accs)

  def distillate(self, mnist, soft_targets, TEMP):

    n_epochs = 50
    batch_size = 50
    n_batches = len(mnist.train.images) // batch_size

    soft_target_ = tf.placeholder(tf.float32, shape = [None, 10])
    T = tf.placeholder(tf.float32)

    # hard target
    y = tf.nn.softmax(self.y_conv)
    # soft target
    y_soft_target = Model.softmax_with_temperature(self.y_conv, temp=T)

    # loss for each of them
    loss_hard_target = tf.reduce_mean(
        -tf.reduce_sum(
            self.y_ * tf.log(y),
            reduction_indices=[1]))

    loss_soft_target = tf.reduce_mean(
        -tf.reduce_sum(
            soft_target_ * tf.log(y_soft_target),
            reduction_indices=[1]))

    # total loss
    loss = loss_soft_target

    # train step
    train_step = tf.train.AdamOptimizer(self.learning_rate).minimize(loss)

    losses = []
    accs = []
    test_accs = []

    with Model.Session() as sess:
      sess.run(tf.global_variables_initializer())
      for epoch in range(n_epochs):
        x_shuffle, y_shuffle, soft_targets_shuffle \
            = shuffle(mnist.train.images, mnist.train.labels, soft_targets)
        for i in range(n_batches):
          start = i * batch_size
          end = start + batch_size
          batch_x, batch_y, batch_soft_targets \
              = x_shuffle[start:end], y_shuffle[start:end], soft_targets_shuffle[start:end]
          sess.run(train_step, feed_dict = {
              self.x: batch_x,
              self.y_: batch_y,
              soft_target_: batch_soft_targets,
              T: TEMP })
        x_shuffle, y_shuffle, soft_targets_shuffle \
            = shuffle(mnist.train.images, mnist.train.labels, soft_targets)
        batch_x, batch_y, batch_soft_targets \
            = x_shuffle[0:1000], y_shuffle[0:1000], soft_targets_shuffle[0:1000]
        train_loss = sess.run(loss, feed_dict = {
            self.x: batch_x,
            self.y_: batch_y,
            soft_target_: batch_soft_targets,
            T: TEMP })
        train_accuracy = sess.run(self.accuracy, feed_dict = {
            self.x: batch_x,
            self.y_: batch_y })
        test_accuracy = sess.run(self.accuracy, feed_dict = {
            self.x: mnist.test.images,
            self.y_: mnist.test.labels })
        print("Distillation: Epoch : %i, Loss : %f, Accuracy: %f, Test accuracy: %f" % (
            epoch + 1, train_loss, train_accuracy, test_accuracy))
        losses.append(train_loss)
        accs.append(train_accuracy)
        test_accs.append(test_accuracy)

        super().append_to_csv("distillation_%d_train_loss" % TEMP, epoch, train_loss)
        super().append_to_csv("distillation_%d_train_accuracy" % TEMP, epoch, train_accuracy)
        super().append_to_csv("distillation_%d_test_accuracy" % TEMP, epoch, test_accuracy)

      super().save(sess)

    return [losses, accs, test_accs]

  def test(self, mnist):
    batch_size = 50
    n_batches = len(mnist.test.images) // batch_size
    C = np.zeros([10, 10])
    prediction = tf.argmax(self.y_conv, 1)
    correct_answer = tf.argmax(self.y_, 1)

    with Model.Session() as sess:
      super().restore(sess)
      print("Accuracy on the test set")
      print(sess.run(self.accuracy, feed_dict = {
          self.x: mnist.test.images,
          self.y_: mnist.test.labels }))
      print("Generating confusion matrix for %s" % self.name)

      for i in range(n_batches):
        start = i * batch_size
        end = start + batch_size
        batch_x = mnist.test.images[start:end]
        batch_y = mnist.test.labels[start:end]
        predict = sess.run(prediction, feed_dict = {
            self.x: batch_x,
            self.y_: batch_y })
        answer = sess.run(correct_answer, feed_dict = {
            self.x: batch_x,
            self.y_: batch_y })
        for (i, j) in zip(predict, answer):
          C[i][j] += 1

    return C

