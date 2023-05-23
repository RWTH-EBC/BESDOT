""" test module sort_product_price.py"""
import utils.sort_product_price as spp


def test_read_table_without_name():
    spp.read_table()


def test_sort_techs():
    price_df = spp.read_table()
    spp.sort_techs(price_df)
