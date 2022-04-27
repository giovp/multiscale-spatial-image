import pytest

from ipfsspec import IPFSFileSystem # type: ignore
import xarray as xr
from zarr.storage import DirectoryStore
from datatree import open_datatree

from spatial_image_multiscale import Method, to_multiscale

IPFS_FS = IPFSFileSystem()
IPFS_CID = "bafybeibpqky6d335duxtkmwowcc6igt2q5qorqd7e5xqfoxlfxm4pozg74"


@pytest.fixture
def input_images():
    result = {}

    store = IPFS_FS.get_mapper(f"ipfs://{IPFS_CID}/input/cthead1.zarr")
    image_ds = xr.open_zarr(store)
    image_da = image_ds.cthead1
    result["cthead1"] = image_da

    store = IPFS_FS.get_mapper(f"ipfs://{IPFS_CID}/input/small_head.zarr")
    image_ds = xr.open_zarr(store)
    image_da = image_ds.small_head
    result["small_head"] = image_da

    return result


def verify_against_baseline(dataset_name, baseline_name, multiscale):
    store = DirectoryStore(f"/home/matt/data/spatial-image-multiscale/baseline/{dataset_name}/{baseline_name}")
    # store = IPFS_FS.get_mapper(
    #     f"ipfs://{IPFS_CID}/baseline/{dataset_name}/{baseline_name}/{idx}"
    # )
    dt = open_datatree(store, engine='zarr')
    xr.testing.assert_equal(dt.ds, multiscale.ds)
    for scale in multiscale.children:
        xr.testing.assert_equal(dt[scale.name].ds, multiscale[scale.name].ds)


def test_base_scale(input_images):
    image = input_images["cthead1"]

    multiscale = to_multiscale(image, [])
    xr.testing.assert_equal(image, multiscale.children[0].ds['cthead1'])

    image = input_images["small_head"]
    multiscale = to_multiscale(image, [])
    xr.testing.assert_equal(image, multiscale.children[0].ds['small_head'])


def test_isotropic_scale_factors(input_images):
    dataset_name = "cthead1"
    image = input_images[dataset_name]
    multiscale = to_multiscale(image, [4, 2])
    verify_against_baseline(dataset_name, "4_2", multiscale)

    dataset_name = "small_head"
    image = input_images[dataset_name]
    multiscale = to_multiscale(image, [3, 2, 2])
    verify_against_baseline(dataset_name, "3_2_2", multiscale)


def test_anisotropic_scale_factors(input_images):
    dataset_name = "cthead1"
    image = input_images[dataset_name]
    scale_factors = [{"x": 2, "y": 4}, {"x": 1, "y": 2}]
    multiscale = to_multiscale(image, scale_factors)
    verify_against_baseline(dataset_name, "x2y4_x1y2", multiscale)

    dataset_name = "small_head"
    image = input_images[dataset_name]
    scale_factors = [
        {"x": 3, "y": 2, "z": 4},
        {"x": 2, "y": 2, "z": 2},
        {"x": 1, "y": 2, "z": 1},
    ]
    multiscale = to_multiscale(image, scale_factors)
    store = DirectoryStore(f'/home/matt/data/spatial-image-multiscale/baseline/{dataset_name}/x3y2z4_x2y2z2_x1y2z1', dimension_separator='/')
    multiscale.to_zarr(store)
    verify_against_baseline(dataset_name, "x3y2z4_x2y2z2_x1y2z1", multiscale)
