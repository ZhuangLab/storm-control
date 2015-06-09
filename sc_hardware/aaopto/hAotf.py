# For interfacing AOTF with HAL
#
# George 5/15

from sc_hardware.crystalTechnologies.hAotf import CrystalTechAOTF
import sc_hardware.aaopto.AOTF as AOTF

class AAAOTF(CrystalTechAOTF):

    def __init__(self, parameters, parent):
	self.aotf = WrappedAOTF()
	CrystalTechAOTF.__init__(self, parameters, parent)
	self.aotf.analogModulationOff()

    def amplitudeOff(self, channel_id):
	self.amplitude_on[channel_id] = False
	aotf_channel = self.channel_parameters[channel_id].channel
	self.aotf.channelOnOff(aotf_channel, False)

    def amplitudeOn(self, channel_id, amplitude):
	self.amplitude_on[channel_id] = True
	aotf_channel = self.channel_parameters[channel_id].channel
	self.aotf.channelOnOff(aotf_channel, True)
	self.aotf.setAmplitude(aotf_channel, amplitude)


class WrappedAOTF(AOTF.AOTF):

    #wrapper functions so that we can use the CrystalTechAOTF base class
    def setFrequencies(self, aotf_channel, frequencies):
	print str(aotf_channel) + " " + str(frequencies)
	self.setFrequency(aotf_channel, frequencies[0])

    def fskOn(self, aotf_channel):
	return 
	#do nothing

    def fskOff(self, aotf_channel):
	return
	#do nothing

