import tensorflow as tf
import numpy as np
from tensorflow.examples.tutorials.mnist import input_data

class Controller:
  def __init__(self, teacher, students, verbose=True):
    self.teacher = teacher
    self.students = students
    self.verbose = verbose

    if self.verbose:
      print("> Loading MNIST data...")
    self.mnist = input_data.read_data_sets('MNIST_data', one_hot = True)

  def trainTeacher(self):
    if self.verbose:
      print("trainingTeacher")
    data = self.teacher.train(self.mnist)
    return data

  def trainStudents(self):
    if self.verbose:
      print("trainingStudents")
    data = []
    for student in self.students:
      data.append({'name': student.name, 'data': student.train(self.mnist)})
    return data

  def distillate(self):
    if self.verbose:
      print("distillating")
    T = [1, 3, 6, 7, 8, 9, 10, 11, 12, 15, 20]
    self.teacher.softTargets(T, self.mnist)
    data = []
    for student in self.students:
      data_student = {'name': student.name, 'data': [] }
      for t in T:
        data_student['data'].append({'t': t, 'data': student.distillate(
            self.mnist,
            np.load("soft-targets-%d.npy" % t),
            t)})
      data.append(data_student)
    return data

  def plotDistillation(self, test_accs, teacher_test_accs, fig_name):
    plt.plot()
    plt.title("MNIST accuracy")
    plt.xlabel("Epochs")
    plt.ylabel("Accuracy")
    plt.plot(range(1, len(test_accs)+1), test_accs, label='Teacher model accuracy')
    plt.plot(range(1, len(teacher_test_accs)+1), teacher_test_accs, label='Student model accuracy')
    plt.legend()
    fig.savefig(fig_name)

  def run(self):
    if self.verbose:
      print("Controller::run")
