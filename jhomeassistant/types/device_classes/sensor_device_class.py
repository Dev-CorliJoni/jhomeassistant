from jhomeassistant.types.device_classes.base_device_class import BaseDeviceClass
from jhomeassistant.types.units import (
    AbsoluteHumidityUnit,
    ApparentPowerUnit,
    AreaUnit,
    AtmosphericPressureUnit,
    BatteryUnit,
    BloodGlucoseConcentrationUnit,
    CarbonDioxideUnit,
    CarbonMonoxideSensorUnit,
    ConductivityUnit,
    CurrentUnit,
    DataRateUnit,
    DataSizeUnit,
    DistanceUnit,
    DurationUnit,
    EnergyUnit,
    EnergyDistanceUnit,
    EnergyStorageUnit,
    FrequencyUnit,
    GasUnit,
    HumidityUnit,
    IlluminanceUnit,
    IrradianceUnit,
    MoistureUnit,
    MonetaryUnit,
    NitrogenDioxideUnit,
    NitrogenMonoxideUnit,
    NitrousOxideUnit,
    OzoneUnit,
    Pm1Unit,
    Pm25Unit,
    Pm4Unit,
    Pm10Unit,
    PowerUnit,
    PowerFactorUnit,
    PrecipitationUnit,
    PrecipitationIntensityUnit,
    PressureSensorUnit,
    ReactiveEnergyUnit,
    ReactivePowerUnit,
    SignalStrengthUnit,
    SoundPressureUnit,
    SpeedUnit,
    SulphurDioxideUnit,
    TemperatureUnit,
    TemperatureDeltaUnit,
    VolatileOrganicCompoundsUnit,
    VolatileOrganicCompoundsPartsUnit,
    VoltageUnit,
    VolumeUnit,
    VolumeFlowRateSensorUnit,
    VolumeStorageUnit,
    WaterUnit,
    WeightUnit,
    WindDirectionUnit,
    WindSpeedUnit,
)


class SensorDeviceClass(BaseDeviceClass):
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
    CONDUCTIVITY = "conductivity"
    DATE = "date"
    ENUM = "enum"
    TEMPERATURE_DELTA = "temperature_delta"
    TIMESTAMP = "timestamp"

    @property
    def unit(self):
        return {
            SensorDeviceClass.ABSOLUTE_HUMIDITY: AbsoluteHumidityUnit,
            SensorDeviceClass.APPARENT_POWER: ApparentPowerUnit,
            SensorDeviceClass.AREA: AreaUnit,
            SensorDeviceClass.ATMOSPHERIC_PRESSURE: AtmosphericPressureUnit,
            SensorDeviceClass.BATTERY: BatteryUnit,
            SensorDeviceClass.BLOOD_GLUCOSE_CONCENTRATION: BloodGlucoseConcentrationUnit,
            SensorDeviceClass.CARBON_DIOXIDE: CarbonDioxideUnit,
            SensorDeviceClass.CURRENT: CurrentUnit,
            SensorDeviceClass.DATA_RATE: DataRateUnit,
            SensorDeviceClass.DATA_SIZE: DataSizeUnit,
            SensorDeviceClass.DISTANCE: DistanceUnit,
            SensorDeviceClass.DURATION: DurationUnit,
            SensorDeviceClass.ENERGY: EnergyUnit,
            SensorDeviceClass.ENERGY_DISTANCE: EnergyDistanceUnit,
            SensorDeviceClass.ENERGY_STORAGE: EnergyStorageUnit,
            SensorDeviceClass.FREQUENCY: FrequencyUnit,
            SensorDeviceClass.GAS: GasUnit,
            SensorDeviceClass.HUMIDITY: HumidityUnit,
            SensorDeviceClass.ILLUMINANCE: IlluminanceUnit,
            SensorDeviceClass.IRRADIANCE: IrradianceUnit,
            SensorDeviceClass.MOISTURE: MoistureUnit,
            SensorDeviceClass.MONETARY: MonetaryUnit,
            SensorDeviceClass.NITROGEN_DIOXIDE: NitrogenDioxideUnit,
            SensorDeviceClass.NITROGEN_MONOXIDE: NitrogenMonoxideUnit,
            SensorDeviceClass.NITROUS_OXIDE: NitrousOxideUnit,
            SensorDeviceClass.OZONE: OzoneUnit,
            SensorDeviceClass.PM1: Pm1Unit,
            SensorDeviceClass.PM25: Pm25Unit,
            SensorDeviceClass.PM4: Pm4Unit,
            SensorDeviceClass.PM10: Pm10Unit,
            SensorDeviceClass.POWER: PowerUnit,
            SensorDeviceClass.POWER_FACTOR: PowerFactorUnit,
            SensorDeviceClass.PRECIPITATION: PrecipitationUnit,
            SensorDeviceClass.PRECIPITATION_INTENSITY: PrecipitationIntensityUnit,
            SensorDeviceClass.REACTIVE_ENERGY: ReactiveEnergyUnit,
            SensorDeviceClass.REACTIVE_POWER: ReactivePowerUnit,
            SensorDeviceClass.SIGNAL_STRENGTH: SignalStrengthUnit,
            SensorDeviceClass.SOUND_PRESSURE: SoundPressureUnit,
            SensorDeviceClass.SPEED: SpeedUnit,
            SensorDeviceClass.SULPHUR_DIOXIDE: SulphurDioxideUnit,
            SensorDeviceClass.TEMPERATURE: TemperatureUnit,
            SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS: VolatileOrganicCompoundsUnit,
            SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS_PARTS: VolatileOrganicCompoundsPartsUnit,
            SensorDeviceClass.VOLTAGE: VoltageUnit,
            SensorDeviceClass.VOLUME: VolumeUnit,
            SensorDeviceClass.VOLUME_STORAGE: VolumeStorageUnit,
            SensorDeviceClass.WATER: WaterUnit,
            SensorDeviceClass.WEIGHT: WeightUnit,
            SensorDeviceClass.WIND_DIRECTION: WindDirectionUnit,
            SensorDeviceClass.WIND_SPEED: WindSpeedUnit,
            SensorDeviceClass.CARBON_MONOXIDE: CarbonMonoxideSensorUnit,
            SensorDeviceClass.CONDUCTIVITY: ConductivityUnit,
            SensorDeviceClass.PRESSURE: PressureSensorUnit,
            SensorDeviceClass.VOLUME_FLOW_RATE: VolumeFlowRateSensorUnit,
            SensorDeviceClass.TEMPERATURE_DELTA: TemperatureDeltaUnit,
        }.get(self, super().unit)
