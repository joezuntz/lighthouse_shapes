class ObjectInputData:

    def __init__(self, object_id, sky_region, centroid, warm_start_data):
        self.object_id = object_id
        self.sky_region = sky_region     # sky area covered by this object: coadd SpanSet? polygon?
        self.centroid = centroid         # position of the object in sky coords
        self.warm_start_data = warm_start_data  # dict of {<algorithm-name>: ObjectAlgorithmData}


class ObjectAlgorithmData:
    """Base class for algorithm results.

    Each algorithm subclass this to capture its results.
    """

    def __init__(self, object_id, sky_region):
        self.object_id = object_id
        self.sky_region = sky_region

    @classmethod
    def get_schema(cls):
        """Return a nested dict of {name: numpy.dtype} for output records
        (assuming one entry per object).
        """
        raise NotImplementedError()

    def as_dict(self):
        """Return a nested dict of values with keys matching the result of
        get_schema() and values coercible to the values of get_schema().
        """
        raise NotImplementedError()

    # To do: how do we save e.g. Monte Carlo samples (and describe their schemas)


class SingleExposureSingleObjectData:
    """Core object representing data needed to fit a single object.

    Will be subclassed by harness to implement realize().
    """

    def __init__(self, object_input_data, region, neighbors):
        self.object_input_data = object_input_data  # ObjectInputData for the object to be fit (shared)
        self.exposure_id
        self.filter = filter                      # string or other identifier for filter name
        self.region = region                      # fine-grained description of pixels to consider (SpanSet)

        # An {object_id: object_input_data} dict of any additional objects
        # that have been determined to overlap this object's exposure_region.
        self.neighbors = neighbors

        # The items below are initialized by realize().
        self.image = None                # (y,x) float array of pixel values
        self.mask = None                 # (y,x) integer array, with bits as mask planes
        self.variance = None             # (y,x) float array of per-pixel variances
        self.local_wcs = None            # assumed locally affine, wavelength-independent
        self.local_psf = None            # PSF as a function of wavelength
        self.local_transmission = None   # photometric scaling as a function of wavelength

    def realize(self):
        """Load additional attributes prior to use in an algorithm.  If
        already loaded, this should be a very fast no-op.
        """
        raise NotImplementedError()


class MultiExposureSingleObjectData:

    def __init__(self, object_input_data, exposure_data):
        self.object_input_data = object_input_data
        self.exposure_data = dict(exposure_data)  # dict of {exposure_id: SingleExposureSingleObjectData}

    # dict-like interface for SingleExposureSingleObjectData, indexed by exposure_id

    # various filtering methods to get e.g. all exposures with a given filter


class SingleExposureMultiObjectData:

    def __init__(self, exposure_id, object_data):
        self.exposure_id = exposure_id
        self.filter = filter
        self.object_data = dict(object_data)      # dict of {object_id: SingleExposureSingleObjectData}

    # dict-like interface for SingleExposureSingleObjectData


class MultiExposureMultiObjectData:
    # conceptually a dict of {(exposure_id, object_id): SingleExposureSingleObjectData},
    # viewable as either a dict of {object_id: MultiExposureSingleObjectData}
    # or a dict of {exposure_id: SingleExposureMultiObjectData}

    def __init__(self, data):
        self.data = dict(data)

    @property
    def by_exposure(self):
        raise NotImplementedError()

    @property
    def by_object(self):
        raise NotImplementedError()

    # dict-like interface indexed on (object_id, exposure_id) tuples


class Deblender:
    """Base class for algorithms that separate objects.

    This could do something as simple as masking out neighbors, or as complex
    as simultaneously fitting everything and subtracting them.
    """

    def __init__(self, config):
        self.config = config

    def processMultiExposure(self, data):
        """Given a MultiExposureMultiObjectData, return a new one with objects
        somehow separated.

        May modify image/variance/mask pixels (e.g. subtract or mask
        neighbors) and exposure_regions.

        Must remove objects from ``neighbors`` dicts to reflect changes it has
        made to the images, but it need not remove all neighbors (i.e. partial
        deblenders are allowed).
        """
        raise NotImplementedError()


class SingleExposureDeblender(Deblender):
    """Specialization of Deblender that can work on one exposure at a time.
    """

    def __init__(self, config):
        Deblender.__init__(self, config)

    def processSingleExposure(self, data):
        """Given a SingleExposureMultiObjectData, return a new one with objects
        somehow separated.

        May modify image/variance/mask pixels (e.g. subtract or mask
        neighbors) and exposure_regions.

        Must remove objects from ``neighbors`` dicts to reflect changes it has
        made to the images, but it need not remove all neighbors (i.e. partial
        deblenders are allowed).
        """
        raise NotImplementedError()

    def processMultiExposure(self, data):
        # Reference implementation with a simple loop - but the point is that
        # an external caller could parallelize this loop.
        result = data.copy()
        for exposure_id, exposure_data in data.by_exposure.items():
            result[exposure_id] = self.processSingleExposure(exposure_data)
        return result


class Fitter:

    def __init__(self, config):
        self.config = config

    def processMultiObject(self, data):
        """Measure the properties of multiple objects simultaneously, from
        a given MultiExposureMultiObjectData.

        Return a dict of {object_id: ObjectAlgorithmData}.
        """
        raise NotImplementedError()


class SingleObjectFitter:

    def __init__(self, config):
        self.config = config

    def processMultiObject(self, data):
        # Reference implementation with a simple loop; harness may parellize
        # this loop.
        result = {}
        for object_id, object_data in data.by_object.items():
            result[object_id] = self.processSingleObject(object_data)
        return result

    def processSingleObject(self, data):
        """Measure the properties of multiple objects simultaneously, from
        a given MultiExposureSingleObjectData.

        Return a single ObjectAlgorithmData.
        """
        raise NotImplementedError()
