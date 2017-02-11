Unified Multi-Exposure Multi-Object Fitting Interface
=====================================================

Concepts:
---------

Harness: the processing system that runs all of this stuff, and works out high-level parallelization and I/O.  Probably different implementations for LSST and DES, or for running on some kinds of simulations vs. running on real data (or simulations that look more like real data).

Deblender: an algorithm that tries to split up objects so they can be processed (more) independently.

Fitter: an algorithm that measures properties of objects; the ultimate goal.

Steps:
------

1. Harness calls a method on each algorithm (deblenders, fitters), giving them coadd data (and associated stuff like WCS, PSF).  This generates the ObjectInputData (including per-algorithm stuff in warm_start_data).  Harness sets sky_region to the union of all the per-algorithm sky regions (algorithms can save their own in warm_start_data).  Also needs to populate the neighbors dict to set which objects need to be processed together (probably via sky_region overlaps, but maybe allow FoF here, too).

2. Harness generates a sequence of unrealized MultiExposureMultiObjectData from a list of ObjectInputData, "percolating" via the neighbors dict.  Harness may choose to realize them now and persist the results to disk so they can be loaded already-realized efficiently later (that's what we'd do with a MEDS backend).

3. Harness runs a combination of Deblenders and Fitters on each MultiExposureMultiObjectData, in parallel.  Each algorithm should call SingleExposureSingleObjectData.realize() on the data it is passed to ensure it is loaded (though this may be a no-op, depending on the harness).  After a Deblender stage, the harness can inspect the neighbors dicts to further subdivide MultiExposureMultiObjectData.  SingleExposureDeblenders can always be parallized further by the harness over exposures, and SingleObjectFitters can be further parallized by the harness over objects.  Regular Deblenders and Fitters are told how many cores they can use and do their own lower-level parallelization.  Set of Deblenders and Fitters is a DAG (probably a very simple one).


Open Questions:
---------------

- What does interface for running on coadds look like?  Should it include detection?

- How do we serialize more complex ObjectOutputData?

- Can we make SingleExposureSingleObjectData handles an explicit part of the interface, to avoid realizing them in memory until we need them?  This could enable harnesses and Fitters that assign each core a group of complete CCD images and sum likelihoods information over the wire (that already works for SingleExposureDeblenders).

- How do we describe a DAG of Deblenders and Fitters (with their configurations)?  Probably use nested dict for configuration; could parse YAML.


Tests:
------

 - How would we reimplement the current MEDS workflow in this scheme?  How would we add an LSST-style deblender to that?
 - Can we do metacalibration with this?
