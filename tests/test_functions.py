import os
import time
import unittest
from typing import List
from unittest import mock

import requests
from pyspark.sql import SparkSession
from requests.exceptions import ConnectionError

from neon.utils.functions import (fake_request, logger, process_data,
                                  retrieve_data)
from neon.utils.sparkutils import establish_spark, group_and_save


class TestAPI(unittest.TestCase):
    """
    All tests for the API itself go here.
    """
    @classmethod
    def setUpClass(cls) -> None:
        cls.logging = logger()
        cls.logging.debug("Starting test session...")
        cls.mocked_data: List[dict] = [{
            "fact": "This is a random fact",
            "length": "-99"
        }, {
            "fact": "This is a fun fact",
            "length": "-98"
        }, {
            "fact": "This is a sad fact",
            "length": "-97"
        }]

    @mock.patch("neon.utils.functions.fake_request", return_value=None)
    def test_retrieve_data_without_waiting(self, patched_request):
        t0 = time.perf_counter()
        actual: dict = retrieve_data(waiting=5)
        actual_keys: list = [key for key in actual]
        expected_keys: list = ["fact", "length"]
        t1 = time.perf_counter() - t0
        self.assertEqual(actual_keys, expected_keys)
        self.assertLess(t1, 5)

    @mock.patch("neon.utils.functions.retrieve_data", return_value={
        "fact": "This is a random fact",
        "length": "-99"
    })
    def test_process_data_with_custom_load(self, patched_retrieve):
        t0 = time.perf_counter()
        actual: list = process_data(usernumber=5, waiting=2)
        expected: list = [{"fact": "This is a random fact", "length": "-99"}]*5
        t1 = time.perf_counter() - t0
        self.assertEqual(actual, expected)
        self.assertLess(t1, 5)


class TestSparkFunctions(unittest.TestCase):
    """
    All tests for Spark-related functions go here.
    """
    @classmethod
    def setUpClass(cls) -> None:
        cls.logging = logger()
        cls.logging.debug("Starting test session...")
        cls.mocked_data: List[dict] = [{
            "fact": "This is a random fact",
            "length": "-99"
        }, {
            "fact": "This is a fun fact",
            "length": "-98"
        }, {
            "fact": "This is a sad fact",
            "length": "-97"
        }]

    def test_group_and_save_with_random_load(self):
        # TODO: make this directory independent
        mocked_save = mock.create_autospec(group_and_save)
        spark: SparkSession = establish_spark(warehouse="./test_warehouse")
        data: List[dict] = self.mocked_data
        expected: bool = mocked_save(spark, data)
        self.assertTrue(expected)

    @mock.patch("pyspark.sql.readwriter.DataFrameWriter.saveAsTable")
    def test_group_and_save_with_patching(self, patched_writer):
        # TODO: make this directory independent
        patched_writer.new = True
        spark: SparkSession = establish_spark(warehouse="./test_warehouse")
        data: List[dict] = self.mocked_data
        group_and_save(spark, data)
        patched_writer.assert_called()

    @mock.patch("neon.utils.functions.fake_request", return_value=None)
    def test_group_and_save_with_api_load(self, patched_request):
        # TODO: make this directory independent
        mocked_save = mock.create_autospec(group_and_save)
        spark: SparkSession = establish_spark(warehouse="./test_warehouse")
        data: list[dict] = process_data(usernumber=5, waiting=2)
        expected: bool = mocked_save(spark, data)
        self.assertTrue(expected)
