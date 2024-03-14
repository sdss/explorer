from specutils import Spectrum1D
from jdaviz import Specviz
from astropy.units import Quantity, Unit, Angstrom

spectral_axis = Quantity(np.linspace(3300, 4001, 1), unit=Angstrom)

flux_unit = Unit("erg/(s cm2 Angstrom)")

flux = Quantity(np.sin(np.linspace(3300, 4001, 1)) + 2, unit=flux_unit)
flux_with_zero = Quantity(np.sin(np.linspace(3300, 4001, 1)) + 1,
                          unit=flux_unit)
mask = flux_with_zero == 0

spectrum = Spectrum1D(spectral_axis=spectral_axis, flux=flux)
spectrum_withzero = Spectrum1D(spectral_axis=spectral_axis,
                               flux=flux_with_zero,
                               mask=mask)

specviz = Specviz()

specviz.load_data(spectrum)
# completely fine!

specviz.show()

specviz.load_data(spectrum_withzero)
# kabooom!!!!!
