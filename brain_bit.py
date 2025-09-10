from neurosdk.callibri_sensor import CallibriSensor
from neurosdk.brainbit_sensor import BrainBitSensor
from neurosdk.brainbit_black_sensor import BrainBitBlackSensor
from neurosdk.headphones_2_sensor import Headphones2Sensor
from neurosdk.headband_sensor import HeadbandSensor
from neurosdk.brainbit_2_sensor import BrainBit2Sensor
from neurosdk.neuro_eeg_sensor import NeuroEEGSensor
from neurosdk.__cmn_types import *
from neurosdk.cmn_types import *
from neurosdk.__utils import raise_exception_if
from neurosdk.sensor import Sensor
from neurosdk.neuro_lib_load import _neuro_lib
from neurosdk.sensor import Sensor
from neurosdk.scanner import Scanner
import numpy as np


class SingleChannel():
    name: str
    values: np.ndarray
    time_vec: np.ndarray
    resistance: np.ndarray


class SensorWithMemory(Sensor):
    t3: SingleChannel
    t4: SingleChannel
    o0: SingleChannel
    o1: SingleChannel

    def __init__(self, sensor_ptr):
        super().__init__(sensor_ptr)
        
    



class WrappedScanner(Scanner):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def create_sensor(self, sensor_info: SensorInfo) -> Sensor:
        """
        Creates an instance of the device according to the information received, and automatically connects to it. The
        connection callback will not be called. If the connection is successful, a Sensor instance will be returned,
        otherwise an exception will be thrown

        :param sensor_info: SensorInfo
            Info about device.
        :return: Sensor
            Connected device object
        :raises BaseException:
            If an internal error occurred while creating device
        """

        status = OpStatus()
        si = NativeSensorInfo()
        si.SensFamily = sensor_info.SensFamily.value
        si.SensModel = sensor_info.SensModel
        si.Name = sensor_info.Name.encode('utf-8')
        si.Address = sensor_info.Address.encode('utf-8')
        si.SerialNumber = sensor_info.SerialNumber.encode('utf-8')
        si.PairingRequired = int(sensor_info.PairingRequired)
        si.RSSI = sensor_info.RSSI

        sensor_ptr = _neuro_lib.createSensor(self.__ptr, si, byref(status))
        raise_exception_if(status)
        family = sensor_info.SensFamily
        if family in (SensorFamily.LECallibri, SensorFamily.LEKolibri):
            return CallibriSensor(sensor_ptr)
        if family is SensorFamily.LEBrainBit:
            return BrainBitSensor(sensor_ptr)
        if family is SensorFamily.LEBrainBitBlack:
            return BrainBitBlackSensor(sensor_ptr)
        if family is SensorFamily.LEHeadPhones2:
            return Headphones2Sensor(sensor_ptr)
        if family is SensorFamily.LEHeadband:
            return HeadbandSensor(sensor_ptr)
        if (family is SensorFamily.LEBrainBit2
                or family is SensorFamily.LEBrainBitPro
                or family is SensorFamily.LEBrainBitFlex):
            return BrainBit2Sensor(sensor_ptr)
        if (family is SensorFamily.LENeuroEEG):
            return NeuroEEGSensor(sensor_ptr)
        return SensorWithMemory(sensor_ptr)
