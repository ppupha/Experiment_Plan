import numpy.random as nr
import sys

from prettytable import PrettyTable
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QMessageBox
from PyQt5 import QtWidgets, uic

import math
from mainwindow import Ui_MainWindow

delta = None


class GaussGenerator:
    def __init__(self, m, sigma, isprint = 0):
        self.m = m
        self.sigma = sigma
        if (isprint):
            print("Normal:")
            print("M = {}".format(self.m))
            print("Sigma = {}".format(self.sigma))

    def generation_time(self):
        return nr.normal(self.m, self.sigma)

class WeibullGenerator:
    def __init__(self, avg, range_, isprint = 0):
        self.k = (range_ / avg) ** (-1.086)
        self.lamda = (avg) / math.gamma(1+1/self.k)

        if (isprint):
            print("Wibull")
            print("K = {}".format(self.k))
            print("Lamda = {}".format(self.lamda))

    def generation_time(self):
        return nr.weibull(self.k) * self.lamda

class RequestGenerator:
    def __init__(self, generator):
        self._generator = generator
        self._receivers = set()
        self.time_times = []

    def add_receiver(self, receiver):
        self._receivers.add(receiver)

    def remove_receiver(self, receiver):
        try:
            self._receivers.remove(receiver)
        except KeyError:
            pass

    def next_time_time(self):
        time = self._generator.generation_time()
        self.time_times.append(time)
        return time

    def emit_request(self):
        for receiver in self._receivers:
            receiver.receive_request()

class RequestProcessor:
    def __init__(self, generator, len_queue=0, reenter_probability=0):
        self._generator = generator
        self._current_queue_size = 0
        self._max_queue_size = 0
        self._processed_requests = 0
        self._reenter_probability = reenter_probability
        self._reentered_requests = 0
        self._len_queue = len_queue
        self._num_lost_requests = 0
        self.time_times = []

    @property
    def processed_requests(self):
        return self._processed_requests

    @property
    def lost_requests(self):
        return self._num_lost_requests

    @property
    def max_queue_size(self):
        return self._max_queue_size

    @property
    def current_queue_size(self):
        return self._current_queue_size

    @property
    def reentered_requests(self):
        return self._reentered_requests

    def process(self):
        if self._current_queue_size > 0:
            time_processed_request.append(current_time)
            self._processed_requests += 1
            self._current_queue_size -= 1

    def receive_request(self):
        self._current_queue_size += 1
        if self._current_queue_size > self._max_queue_size:
            self._max_queue_size += 1

    def next_time_time(self):
        time = self._generator.generation_time()
        self.time_times.append(time)
        return time


current_time = 0
time_processed_request = []


class Modeller:
    def __init__(self, generator, processor):
        self._generator = generator
        self._processor = processor
        self._generator.add_receiver(self._processor)

    def event_based_modelling(self, time_modelling):
        global current_time
        global time_processed_request
        global p_teor
        queue_size = [0]
        time_generated_request = []
        num_requests = [0]
        
        generator = self._generator
        processor = self._processor

        gen_time = generator.next_time_time()
        proc_time = gen_time + processor.next_time_time()
        #while processor.processed_requests < request_count:
        while current_time < time_modelling:
            num = num_requests[-1]
            if gen_time <= proc_time:
                current_time = gen_time
                time_generated_request.append(current_time)
                generator.emit_request()
                num += 1
                gen_time += generator.next_time_time()
            else:
                current_time = proc_time 
                if processor.current_queue_size > 0:
                    num -= 1
                processor.process()
                if processor.current_queue_size > 0:
                    proc_time += processor.next_time_time()
                else:
                    proc_time = gen_time + processor.next_time_time()
                queue_size.append(processor.current_queue_size)

            num_requests.append(num)

        # интенсивность генератора
        lambda_fact = 1 / (sum(generator.time_times) / len(generator.time_times))

        # интенсивность обработчика
        mu_fact = 1 / (sum(processor.time_times) / len(processor.time_times))
        p = lambda_fact / mu_fact
        num_reports_teor = p / (1 - p)
        num_reports_fact = sum(queue_size) / len(queue_size)
        k = num_reports_fact / num_reports_teor

        if p_teor >= 1 or p_teor <= 0 or k == 0:
            k = 1

        if (len(time_processed_request)):
            mas_time_request_in_smo = []
            for i in range(len(time_processed_request)):
                mas_time_request_in_smo.append(time_processed_request[i] - time_generated_request[i])
            avg_time_in_smo = sum(mas_time_request_in_smo) / len(mas_time_request_in_smo) / k
        else:
            avg_time_in_smo = 0

        result = [
            processor.processed_requests,
            processor.reentered_requests,
            processor.max_queue_size,
            current_time,
            sum(queue_size) / len(queue_size),
            lambda_fact,
            mu_fact,
            avg_time_in_smo
        ]
        return result

        return (processor.processed_requests, processor.reentered_requests,
                processor.max_queue_size, proc_time)

    def time_based_modelling(self, dt, time_modelling):
        global current_time
        global time_processed_request
        global p_teor
        time_processed_request.clear()
        current_time = 0
        generator = self._generator
        processor = self._processor
        queue_size = [0]
        time_generated_request = []
        num_requests = [0]

        gen_time = generator.next_time_time()
        proc_time = gen_time + processor.next_time_time()

        while current_time < time_modelling :
            num = num_requests[-1]
            if gen_time <= current_time:
                time_generated_request.append(current_time)
                generator.emit_request()
                num += 1
                gen_time += generator.next_time_time()
            if proc_time <= current_time:
                if processor.current_queue_size > 0:
                    num -= 1
                processor.process()

                if processor.current_queue_size > 0:
                    proc_time += processor.next_time_time()
                else:
                    proc_time = gen_time + processor.next_time_time()
            queue_size.append(processor.current_queue_size)


            current_time += dt
            num_requests.append(num)

        # интенсивность генератора
        lambda_fact = 1 / (sum(generator.time_times) / len(generator.time_times))

        # интенсивность обработчика
        mu_fact = 1 / (sum(processor.time_times) / len(processor.time_times))
        p = lambda_fact / mu_fact
        num_reports_teor = p / (1 - p)
        num_reports_fact = sum(queue_size) / len(queue_size)
        k = num_reports_fact / num_reports_teor

        if p_teor >= 1 or p_teor <= 0 or k == 0:
            k = 1

        if (len(time_processed_request)):
            mas_time_request_in_smo = []
            for i in range(len(time_processed_request)):
                mas_time_request_in_smo.append(time_processed_request[i] - time_generated_request[i])
            avg_time_in_smo = sum(mas_time_request_in_smo) / len(mas_time_request_in_smo) / k
        else:
            avg_time_in_smo = 0

        result = [
            processor.processed_requests,
            processor.reentered_requests,
            processor.max_queue_size,
            current_time,
            sum(queue_size) / len(queue_size),
            lambda_fact,
            mu_fact,
            avg_time_in_smo
        ]
        return result


p_teor = 0


class mywindow(QMainWindow):
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        uic.loadUi("mainwindow.ui", self)

        self.pushButton_model.clicked.connect(self.onModelBtnClick)
        self.pushButton_graph.clicked.connect(self.onGraphBtnClick)

    def addItemTableWidget(self, row, column, value):
        item = QTableWidgetItem()
        item.setText(str(value))
        self.tableWidget.setItem(row, column, item)

    def onModelBtnClick(self):
        try:
            global p_teor
            intensivity_gen = self.spinbox_intensivity_gen.value()
            range_gen = self.spinbox_intensivity_proc_range.value()
            intensivity_proc = self.spinbox_intensivity_oa.value()
            range_proc = self.spinbox_intensivity_oa_range.value()
            time_modelling = self.spinbox_time_model.value()

            step = 0.1

            generator = RequestGenerator(GaussGenerator(1 / intensivity_gen, range_gen))
            processor = RequestProcessor(WeibullGenerator(1 / intensivity_proc, range_proc))
            
            model = Modeller(generator, processor)
            result_tb = model.event_based_modelling(time_modelling)

            p = p_teor = intensivity_gen / intensivity_proc

            self.addItemTableWidget(0, 0, round(p, 2))
            self.addItemTableWidget(0, 1, round(result_tb[5] / result_tb[6], 3))

            if 0 < p < 1:
                self.addItemTableWidget(1, 0, round(p / (1 - p) / intensivity_gen, 2))
            else:
                self.addItemTableWidget(1, 0, 6 * '-')
            self.addItemTableWidget(1, 1, round(result_tb[7], 5))

            self.addItemTableWidget(2, 0, 6 * '-')
            self.addItemTableWidget(2, 1, result_tb[0])

            self.addItemTableWidget(3, 0, time_modelling)
            self.addItemTableWidget(3, 1, round(result_tb[3], 3))

        except Exception as e:
            msgBox = QMessageBox()
            msgBox.setText('Произошла ошибка!\n' + repr(e))
            msgBox.show()
            msgBox.exec()

    def onGraphBtnClick(self):
        i = 0.01
        mas = []
        res = []
        delta = None
        while i < 1.3:
            print("i = {}".format(i))
            mas_j = []
            
            step = 0.1
            time_modelling = 1000
            intensivity_gen = i
            range_gen = 1
            intensivity_proc = 1
            range_proc = 1
                
            generator = RequestGenerator(GaussGenerator(1 / intensivity_gen, range_gen, 1))
            processor = RequestProcessor(WeibullGenerator(1 / intensivity_proc, range_proc, 1))
            print("Test")
            for j in range(500):
                generator = RequestGenerator(GaussGenerator(1 / intensivity_gen, range_gen))
                processor = RequestProcessor(WeibullGenerator(1 / intensivity_proc, range_proc))
                model = Modeller(generator, processor)
                result_tb = model.time_based_modelling(step, time_modelling)
                result = result_tb[7]#result_tb[5] / result_tb[6]
                    
                mas_j.append(result)
            mas.append(i)
            r = sum(mas_j)/len(mas_j)
            print("res = {}".format(r))
            if (delta == None):
                delta = r
            r = r - delta
            res.append(r)
            mas_j.clear()
            

            if i < 0.1:
                i += 0.1
            else:
                i += 0.1
            
        plt.plot(mas, res)
        plt.grid()
        plt.ylabel('Время пребывания заявки в СМО')
        plt.xlabel('Загрузка системы')
        plt.show()


if __name__ == "__main__":
    app = QApplication([])
    application = mywindow()
    application.show()

    sys.exit(app.exec())
