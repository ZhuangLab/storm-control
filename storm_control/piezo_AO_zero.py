if __name__ == "__main__":
    import nidaqmx
    with nidaqmx.Task() as task:
        dev = "Dev2/ao0"
        volt = 0
        task.ao_channels.add_ao_voltage_chan(dev)
        task.write(volt, auto_start = True)
        print("Piezo on", dev, "set to:", volt, "volts")