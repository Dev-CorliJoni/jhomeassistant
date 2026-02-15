from jhomeassistant.types.device_classes.base_device_class import BaseDeviceClass
from jhomeassistant.types.units import AbsoluteHumidityUnit, ApparentPowerUnit, AreaUnit, AtmosphericPressureUnit, \
    BatteryUnit, BloodGlucoseConcentrationUnit, CarbonDioxideUnit, CarbonMonoxideNumberUnit, CurrentUnit, DataRateUnit, \
    DataSizeUnit, DistanceUnit, DurationUnit, EnergyUnit, EnergyDistanceUnit, EnergyStorageUnit, FrequencyUnit, \
    GasUnit, HumidityUnit, IlluminanceUnit, IrradianceUnit, MoistureUnit, MonetaryUnit, NitrogenDioxideUnit, \
    NitrogenMonoxideUnit, NitrousOxideUnit, OzoneUnit, Pm1Unit, Pm25Unit, Pm4Unit, Pm10Unit, PowerUnit, \
    PowerFactorUnit, PrecipitationUnit, PrecipitationIntensityUnit, PressureNumberUnit, ReactiveEnergyUnit, \
    ReactivePowerUnit, SignalStrengthUnit, SoundPressureUnit, SpeedUnit, SulphurDioxideUnit, TemperatureUnit, \
    VolatileOrganicCompoundsUnit, VolatileOrganicCompoundsPartsUnit, VoltageUnit, VolumeUnit, VolumeFlowRateNumberUnit, \
    VolumeStorageUnit, WaterUnit, WeightUnit, WindDirectionUnit, WindSpeedUnit


class NumberDeviceClass(BaseDeviceClass):
    NONE = None
    ABSOLUTE_HUMIDITY = "absolute_humidity"
    APPARENT_POWER = "apparent_power"
    AQI = "aqi"
    AREA = "area"
    ATMOSPHERIC_PRESSURE = "atmospheric_pressure"
    BATTERY = "battery"
    BLOOD_GLUCOSE_CONCENTRATION = "blood_glucose_concentration"
    CARBON_DIOXIDE = "carbon_dioxide"
    CARBON_MONOXIDE = "carbon_monoxide"
    CURRENT = "current"
    DATA_RATE = "data_rate"
    DATA_SIZE = "data_size"
    DISTANCE = "distance"
    DURATION = "duration"
    ENERGY = "energy"
    ENERGY_DISTANCE = "energy_distance"
    ENERGY_STORAGE = "energy_storage"
    FREQUENCY = "frequency"
    GAS = "gas"
    HUMIDITY = "humidity"
    ILLUMINANCE = "illuminance"
    IRRADIANCE = "irradiance"
    MOISTURE = "moisture"
    MONETARY = "monetary"
    NITROGEN_DIOXIDE = "nitrogen_dioxide"
    NITROGEN_MONOXIDE = "nitrogen_monoxide"
    NITROUS_OXIDE = "nitrous_oxide"
    OZONE = "ozone"
    PH = "ph"
    PM1 = "pm1"
    PM25 = "pm25"
    PM4 = "pm4"
    PM10 = "pm10"
    POWER = "power"
    POWER_FACTOR = "power_factor"
    PRECIPITATION = "precipitation"
    PRECIPITATION_INTENSITY = "precipitation_intensity"
    PRESSURE = "pressure"
    REACTIVE_ENERGY = "reactive_energy"
    REACTIVE_POWER = "reactive_power"
    SIGNAL_STRENGTH = "signal_strength"
    SOUND_PRESSURE = "sound_pressure"
    SPEED = "speed"
    SULPHUR_DIOXIDE = "sulphur_dioxide"
    TEMPERATURE = "temperature"
    VOLATILE_ORGANIC_COMPOUNDS = "volatile_organic_compounds"
    VOLATILE_ORGANIC_COMPOUNDS_PARTS = "volatile_organic_compounds_parts"
    VOLTAGE = "voltage"
    VOLUME = "volume"
    VOLUME_FLOW_RATE = "volume_flow_rate"
    VOLUME_STORAGE = "volume_storage"
    WATER = "water"
    WEIGHT = "weight"
    WIND_DIRECTION = "wind_direction"
    WIND_SPEED = "wind_speed"

    @property
    def unit(self):
        return {
            NumberDeviceClass.ABSOLUTE_HUMIDITY: AbsoluteHumidityUnit,
            NumberDeviceClass.APPARENT_POWER: ApparentPowerUnit,
            NumberDeviceClass.AREA: AreaUnit,
            NumberDeviceClass.ATMOSPHERIC_PRESSURE: AtmosphericPressureUnit,
            NumberDeviceClass.BATTERY: BatteryUnit,
            NumberDeviceClass.BLOOD_GLUCOSE_CONCENTRATION: BloodGlucoseConcentrationUnit,
            NumberDeviceClass.CARBON_DIOXIDE: CarbonDioxideUnit,
            NumberDeviceClass.CARBON_MONOXIDE: CarbonMonoxideNumberUnit,
            NumberDeviceClass.CURRENT: CurrentUnit,
            NumberDeviceClass.DATA_RATE: DataRateUnit,
            NumberDeviceClass.DATA_SIZE: DataSizeUnit,
            NumberDeviceClass.DISTANCE: DistanceUnit,
            NumberDeviceClass.DURATION: DurationUnit,
            NumberDeviceClass.ENERGY: EnergyUnit,
            NumberDeviceClass.ENERGY_DISTANCE: EnergyDistanceUnit,
            NumberDeviceClass.ENERGY_STORAGE: EnergyStorageUnit,
            NumberDeviceClass.FREQUENCY: FrequencyUnit,
            NumberDeviceClass.GAS: GasUnit,
            NumberDeviceClass.HUMIDITY: HumidityUnit,
            NumberDeviceClass.ILLUMINANCE: IlluminanceUnit,
            NumberDeviceClass.IRRADIANCE: IrradianceUnit,
            NumberDeviceClass.MOISTURE: MoistureUnit,
            NumberDeviceClass.MONETARY: MonetaryUnit,
            NumberDeviceClass.NITROGEN_DIOXIDE: NitrogenDioxideUnit,
            NumberDeviceClass.NITROGEN_MONOXIDE: NitrogenMonoxideUnit,
            NumberDeviceClass.NITROUS_OXIDE: NitrousOxideUnit,
            NumberDeviceClass.OZONE: OzoneUnit,
            NumberDeviceClass.PM1: Pm1Unit,
            NumberDeviceClass.PM25: Pm25Unit,
            NumberDeviceClass.PM4: Pm4Unit,
            NumberDeviceClass.PM10: Pm10Unit,
            NumberDeviceClass.POWER: PowerUnit,
            NumberDeviceClass.POWER_FACTOR: PowerFactorUnit,
            NumberDeviceClass.PRECIPITATION: PrecipitationUnit,
            NumberDeviceClass.PRECIPITATION_INTENSITY: PrecipitationIntensityUnit,
            NumberDeviceClass.PRESSURE: PressureNumberUnit,
            NumberDeviceClass.REACTIVE_ENERGY: ReactiveEnergyUnit,
            NumberDeviceClass.REACTIVE_POWER: ReactivePowerUnit,
            NumberDeviceClass.SIGNAL_STRENGTH: SignalStrengthUnit,
            NumberDeviceClass.SOUND_PRESSURE: SoundPressureUnit,
            NumberDeviceClass.SPEED: SpeedUnit,
            NumberDeviceClass.SULPHUR_DIOXIDE: SulphurDioxideUnit,
            NumberDeviceClass.TEMPERATURE: TemperatureUnit,
            NumberDeviceClass.VOLATILE_ORGANIC_COMPOUNDS: VolatileOrganicCompoundsUnit,
            NumberDeviceClass.VOLATILE_ORGANIC_COMPOUNDS_PARTS: VolatileOrganicCompoundsPartsUnit,
            NumberDeviceClass.VOLTAGE: VoltageUnit,
            NumberDeviceClass.VOLUME: VolumeUnit,
            NumberDeviceClass.VOLUME_FLOW_RATE: VolumeFlowRateNumberUnit,
            NumberDeviceClass.VOLUME_STORAGE: VolumeStorageUnit,
            NumberDeviceClass.WATER: WaterUnit,
            NumberDeviceClass.WEIGHT: WeightUnit,
            NumberDeviceClass.WIND_DIRECTION: WindDirectionUnit,
            NumberDeviceClass.WIND_SPEED: WindSpeedUnit
        }.get(self, super().unit)
