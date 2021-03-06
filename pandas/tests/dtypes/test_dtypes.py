# -*- coding: utf-8 -*-
import re
import pytest

from itertools import product

import numpy as np
import pandas as pd
from pandas import (
    Series, Categorical, CategoricalIndex, IntervalIndex, date_range)

from pandas.compat import string_types
from pandas.core.arrays import ExtensionArray
from pandas.core.dtypes.dtypes import (
    DatetimeTZDtype, PeriodDtype,
    IntervalDtype, CategoricalDtype, ExtensionDtype)
from pandas.core.dtypes.common import (
    is_categorical_dtype, is_categorical,
    is_datetime64tz_dtype, is_datetimetz,
    is_extension_array_dtype,
    is_period_dtype, is_period,
    is_dtype_equal, is_datetime64_ns_dtype,
    is_datetime64_dtype, is_interval_dtype,
    is_datetime64_any_dtype, is_string_dtype,
    _coerce_to_dtype)
import pandas.util.testing as tm


class Base(object):

    def setup_method(self, method):
        self.dtype = self.create()

    def test_hash(self):
        hash(self.dtype)

    def test_equality_invalid(self):
        assert not self.dtype == 'foo'
        assert not is_dtype_equal(self.dtype, np.int64)

    def test_numpy_informed(self):
        pytest.raises(TypeError, np.dtype, self.dtype)

        assert not self.dtype == np.str_
        assert not np.str_ == self.dtype

    def test_pickle(self):
        # make sure our cache is NOT pickled

        # clear the cache
        type(self.dtype).reset_cache()
        assert not len(self.dtype._cache)

        # force back to the cache
        result = tm.round_trip_pickle(self.dtype)
        assert not len(self.dtype._cache)
        assert result == self.dtype


class TestCategoricalDtype(Base):

    def create(self):
        return CategoricalDtype()

    def test_pickle(self):
        # make sure our cache is NOT pickled

        # clear the cache
        type(self.dtype).reset_cache()
        assert not len(self.dtype._cache)

        # force back to the cache
        result = tm.round_trip_pickle(self.dtype)
        assert result == self.dtype

    def test_hash_vs_equality(self):
        dtype = self.dtype
        dtype2 = CategoricalDtype()
        assert dtype == dtype2
        assert dtype2 == dtype
        assert hash(dtype) == hash(dtype2)

    def test_equality(self):
        assert is_dtype_equal(self.dtype, 'category')
        assert is_dtype_equal(self.dtype, CategoricalDtype())
        assert not is_dtype_equal(self.dtype, 'foo')

    def test_construction_from_string(self):
        result = CategoricalDtype.construct_from_string('category')
        assert is_dtype_equal(self.dtype, result)
        pytest.raises(
            TypeError, lambda: CategoricalDtype.construct_from_string('foo'))

    def test_constructor_invalid(self):
        with tm.assert_raises_regex(TypeError,
                                    "CategoricalIndex.* must be called"):
            CategoricalDtype("category")

    def test_is_dtype(self):
        assert CategoricalDtype.is_dtype(self.dtype)
        assert CategoricalDtype.is_dtype('category')
        assert CategoricalDtype.is_dtype(CategoricalDtype())
        assert not CategoricalDtype.is_dtype('foo')
        assert not CategoricalDtype.is_dtype(np.float64)

    def test_basic(self):

        assert is_categorical_dtype(self.dtype)

        factor = Categorical(['a', 'b', 'b', 'a', 'a', 'c', 'c', 'c'])

        s = Series(factor, name='A')

        # dtypes
        assert is_categorical_dtype(s.dtype)
        assert is_categorical_dtype(s)
        assert not is_categorical_dtype(np.dtype('float64'))

        assert is_categorical(s.dtype)
        assert is_categorical(s)
        assert not is_categorical(np.dtype('float64'))
        assert not is_categorical(1.0)

    def test_tuple_categories(self):
        categories = [(1, 'a'), (2, 'b'), (3, 'c')]
        result = CategoricalDtype(categories)
        assert all(result.categories == categories)

    @pytest.mark.parametrize('dtype', [
        CategoricalDtype(list('abc'), False),
        CategoricalDtype(list('abc'), True)])
    @pytest.mark.parametrize('new_dtype', [
        'category',
        CategoricalDtype(None, False),
        CategoricalDtype(None, True),
        CategoricalDtype(list('abc'), False),
        CategoricalDtype(list('abc'), True),
        CategoricalDtype(list('cba'), False),
        CategoricalDtype(list('cba'), True),
        CategoricalDtype(list('wxyz'), False),
        CategoricalDtype(list('wxyz'), True)])
    def test_update_dtype(self, dtype, new_dtype):
        if isinstance(new_dtype, string_types) and new_dtype == 'category':
            expected_categories = dtype.categories
            expected_ordered = dtype.ordered
        else:
            expected_categories = new_dtype.categories
            if expected_categories is None:
                expected_categories = dtype.categories
            expected_ordered = new_dtype.ordered

        result = dtype._update_dtype(new_dtype)
        tm.assert_index_equal(result.categories, expected_categories)
        assert result.ordered is expected_ordered

    @pytest.mark.parametrize('bad_dtype', [
        'foo', object, np.int64, PeriodDtype('Q')])
    def test_update_dtype_errors(self, bad_dtype):
        dtype = CategoricalDtype(list('abc'), False)
        msg = 'a CategoricalDtype must be passed to perform an update, '
        with tm.assert_raises_regex(ValueError, msg):
            dtype._update_dtype(bad_dtype)


class TestDatetimeTZDtype(Base):

    def create(self):
        return DatetimeTZDtype('ns', 'US/Eastern')

    def test_hash_vs_equality(self):
        # make sure that we satisfy is semantics
        dtype = self.dtype
        dtype2 = DatetimeTZDtype('ns', 'US/Eastern')
        dtype3 = DatetimeTZDtype(dtype2)
        assert dtype == dtype2
        assert dtype2 == dtype
        assert dtype3 == dtype
        assert dtype is dtype2
        assert dtype2 is dtype
        assert dtype3 is dtype
        assert hash(dtype) == hash(dtype2)
        assert hash(dtype) == hash(dtype3)

    def test_construction(self):
        pytest.raises(ValueError,
                      lambda: DatetimeTZDtype('ms', 'US/Eastern'))

    def test_subclass(self):
        a = DatetimeTZDtype('datetime64[ns, US/Eastern]')
        b = DatetimeTZDtype('datetime64[ns, CET]')

        assert issubclass(type(a), type(a))
        assert issubclass(type(a), type(b))

    def test_coerce_to_dtype(self):
        assert (_coerce_to_dtype('datetime64[ns, US/Eastern]') ==
                DatetimeTZDtype('ns', 'US/Eastern'))
        assert (_coerce_to_dtype('datetime64[ns, Asia/Tokyo]') ==
                DatetimeTZDtype('ns', 'Asia/Tokyo'))

    def test_compat(self):
        assert is_datetime64tz_dtype(self.dtype)
        assert is_datetime64tz_dtype('datetime64[ns, US/Eastern]')
        assert is_datetime64_any_dtype(self.dtype)
        assert is_datetime64_any_dtype('datetime64[ns, US/Eastern]')
        assert is_datetime64_ns_dtype(self.dtype)
        assert is_datetime64_ns_dtype('datetime64[ns, US/Eastern]')
        assert not is_datetime64_dtype(self.dtype)
        assert not is_datetime64_dtype('datetime64[ns, US/Eastern]')

    def test_construction_from_string(self):
        result = DatetimeTZDtype('datetime64[ns, US/Eastern]')
        assert is_dtype_equal(self.dtype, result)
        result = DatetimeTZDtype.construct_from_string(
            'datetime64[ns, US/Eastern]')
        assert is_dtype_equal(self.dtype, result)
        pytest.raises(TypeError,
                      lambda: DatetimeTZDtype.construct_from_string('foo'))

    def test_is_dtype(self):
        assert not DatetimeTZDtype.is_dtype(None)
        assert DatetimeTZDtype.is_dtype(self.dtype)
        assert DatetimeTZDtype.is_dtype('datetime64[ns, US/Eastern]')
        assert not DatetimeTZDtype.is_dtype('foo')
        assert DatetimeTZDtype.is_dtype(DatetimeTZDtype('ns', 'US/Pacific'))
        assert not DatetimeTZDtype.is_dtype(np.float64)

    def test_equality(self):
        assert is_dtype_equal(self.dtype, 'datetime64[ns, US/Eastern]')
        assert is_dtype_equal(self.dtype, DatetimeTZDtype('ns', 'US/Eastern'))
        assert not is_dtype_equal(self.dtype, 'foo')
        assert not is_dtype_equal(self.dtype, DatetimeTZDtype('ns', 'CET'))
        assert not is_dtype_equal(DatetimeTZDtype('ns', 'US/Eastern'),
                                  DatetimeTZDtype('ns', 'US/Pacific'))

        # numpy compat
        assert is_dtype_equal(np.dtype("M8[ns]"), "datetime64[ns]")

    def test_basic(self):

        assert is_datetime64tz_dtype(self.dtype)

        dr = date_range('20130101', periods=3, tz='US/Eastern')
        s = Series(dr, name='A')

        # dtypes
        assert is_datetime64tz_dtype(s.dtype)
        assert is_datetime64tz_dtype(s)
        assert not is_datetime64tz_dtype(np.dtype('float64'))
        assert not is_datetime64tz_dtype(1.0)

        assert is_datetimetz(s)
        assert is_datetimetz(s.dtype)
        assert not is_datetimetz(np.dtype('float64'))
        assert not is_datetimetz(1.0)

    def test_dst(self):

        dr1 = date_range('2013-01-01', periods=3, tz='US/Eastern')
        s1 = Series(dr1, name='A')
        assert is_datetimetz(s1)

        dr2 = date_range('2013-08-01', periods=3, tz='US/Eastern')
        s2 = Series(dr2, name='A')
        assert is_datetimetz(s2)
        assert s1.dtype == s2.dtype

    def test_parser(self):
        # pr #11245
        for tz, constructor in product(('UTC', 'US/Eastern'),
                                       ('M8', 'datetime64')):
            assert (DatetimeTZDtype('%s[ns, %s]' % (constructor, tz)) ==
                    DatetimeTZDtype('ns', tz))

    def test_empty(self):
        dt = DatetimeTZDtype()
        with pytest.raises(AttributeError):
            str(dt)


class TestPeriodDtype(Base):

    def create(self):
        return PeriodDtype('D')

    def test_hash_vs_equality(self):
        # make sure that we satisfy is semantics
        dtype = self.dtype
        dtype2 = PeriodDtype('D')
        dtype3 = PeriodDtype(dtype2)
        assert dtype == dtype2
        assert dtype2 == dtype
        assert dtype3 == dtype
        assert dtype is dtype2
        assert dtype2 is dtype
        assert dtype3 is dtype
        assert hash(dtype) == hash(dtype2)
        assert hash(dtype) == hash(dtype3)

    def test_construction(self):
        with pytest.raises(ValueError):
            PeriodDtype('xx')

        for s in ['period[D]', 'Period[D]', 'D']:
            dt = PeriodDtype(s)
            assert dt.freq == pd.tseries.offsets.Day()
            assert is_period_dtype(dt)

        for s in ['period[3D]', 'Period[3D]', '3D']:
            dt = PeriodDtype(s)
            assert dt.freq == pd.tseries.offsets.Day(3)
            assert is_period_dtype(dt)

        for s in ['period[26H]', 'Period[26H]', '26H',
                  'period[1D2H]', 'Period[1D2H]', '1D2H']:
            dt = PeriodDtype(s)
            assert dt.freq == pd.tseries.offsets.Hour(26)
            assert is_period_dtype(dt)

    def test_subclass(self):
        a = PeriodDtype('period[D]')
        b = PeriodDtype('period[3D]')

        assert issubclass(type(a), type(a))
        assert issubclass(type(a), type(b))

    def test_identity(self):
        assert PeriodDtype('period[D]') == PeriodDtype('period[D]')
        assert PeriodDtype('period[D]') is PeriodDtype('period[D]')

        assert PeriodDtype('period[3D]') == PeriodDtype('period[3D]')
        assert PeriodDtype('period[3D]') is PeriodDtype('period[3D]')

        assert PeriodDtype('period[1S1U]') == PeriodDtype('period[1000001U]')
        assert PeriodDtype('period[1S1U]') is PeriodDtype('period[1000001U]')

    def test_coerce_to_dtype(self):
        assert _coerce_to_dtype('period[D]') == PeriodDtype('period[D]')
        assert _coerce_to_dtype('period[3M]') == PeriodDtype('period[3M]')

    def test_compat(self):
        assert not is_datetime64_ns_dtype(self.dtype)
        assert not is_datetime64_ns_dtype('period[D]')
        assert not is_datetime64_dtype(self.dtype)
        assert not is_datetime64_dtype('period[D]')

    def test_construction_from_string(self):
        result = PeriodDtype('period[D]')
        assert is_dtype_equal(self.dtype, result)
        result = PeriodDtype.construct_from_string('period[D]')
        assert is_dtype_equal(self.dtype, result)
        with pytest.raises(TypeError):
            PeriodDtype.construct_from_string('foo')
        with pytest.raises(TypeError):
            PeriodDtype.construct_from_string('period[foo]')
        with pytest.raises(TypeError):
            PeriodDtype.construct_from_string('foo[D]')

        with pytest.raises(TypeError):
            PeriodDtype.construct_from_string('datetime64[ns]')
        with pytest.raises(TypeError):
            PeriodDtype.construct_from_string('datetime64[ns, US/Eastern]')

    def test_is_dtype(self):
        assert PeriodDtype.is_dtype(self.dtype)
        assert PeriodDtype.is_dtype('period[D]')
        assert PeriodDtype.is_dtype('period[3D]')
        assert PeriodDtype.is_dtype(PeriodDtype('3D'))
        assert PeriodDtype.is_dtype('period[U]')
        assert PeriodDtype.is_dtype('period[S]')
        assert PeriodDtype.is_dtype(PeriodDtype('U'))
        assert PeriodDtype.is_dtype(PeriodDtype('S'))

        assert not PeriodDtype.is_dtype('D')
        assert not PeriodDtype.is_dtype('3D')
        assert not PeriodDtype.is_dtype('U')
        assert not PeriodDtype.is_dtype('S')
        assert not PeriodDtype.is_dtype('foo')
        assert not PeriodDtype.is_dtype(np.object_)
        assert not PeriodDtype.is_dtype(np.int64)
        assert not PeriodDtype.is_dtype(np.float64)

    def test_equality(self):
        assert is_dtype_equal(self.dtype, 'period[D]')
        assert is_dtype_equal(self.dtype, PeriodDtype('D'))
        assert is_dtype_equal(self.dtype, PeriodDtype('D'))
        assert is_dtype_equal(PeriodDtype('D'), PeriodDtype('D'))

        assert not is_dtype_equal(self.dtype, 'D')
        assert not is_dtype_equal(PeriodDtype('D'), PeriodDtype('2D'))

    def test_basic(self):
        assert is_period_dtype(self.dtype)

        pidx = pd.period_range('2013-01-01 09:00', periods=5, freq='H')

        assert is_period_dtype(pidx.dtype)
        assert is_period_dtype(pidx)
        assert is_period(pidx)

        s = Series(pidx, name='A')
        # dtypes
        # series results in object dtype currently,
        # is_period checks period_arraylike
        assert not is_period_dtype(s.dtype)
        assert not is_period_dtype(s)
        assert is_period(s)

        assert not is_period_dtype(np.dtype('float64'))
        assert not is_period_dtype(1.0)
        assert not is_period(np.dtype('float64'))
        assert not is_period(1.0)

    def test_empty(self):
        dt = PeriodDtype()
        with pytest.raises(AttributeError):
            str(dt)

    def test_not_string(self):
        # though PeriodDtype has object kind, it cannot be string
        assert not is_string_dtype(PeriodDtype('D'))


class TestIntervalDtype(Base):

    def create(self):
        return IntervalDtype('int64')

    def test_hash_vs_equality(self):
        # make sure that we satisfy is semantics
        dtype = self.dtype
        dtype2 = IntervalDtype('int64')
        dtype3 = IntervalDtype(dtype2)
        assert dtype == dtype2
        assert dtype2 == dtype
        assert dtype3 == dtype
        assert dtype is dtype2
        assert dtype2 is dtype3
        assert dtype3 is dtype
        assert hash(dtype) == hash(dtype2)
        assert hash(dtype) == hash(dtype3)

        dtype1 = IntervalDtype('interval')
        dtype2 = IntervalDtype(dtype1)
        dtype3 = IntervalDtype('interval')
        assert dtype2 == dtype1
        assert dtype2 == dtype2
        assert dtype2 == dtype3
        assert dtype2 is dtype1
        assert dtype2 is dtype2
        assert dtype2 is dtype3
        assert hash(dtype2) == hash(dtype1)
        assert hash(dtype2) == hash(dtype2)
        assert hash(dtype2) == hash(dtype3)

    @pytest.mark.parametrize('subtype', [
        'interval[int64]', 'Interval[int64]', 'int64', np.dtype('int64')])
    def test_construction(self, subtype):
        i = IntervalDtype(subtype)
        assert i.subtype == np.dtype('int64')
        assert is_interval_dtype(i)

    @pytest.mark.parametrize('subtype', [None, 'interval', 'Interval'])
    def test_construction_generic(self, subtype):
        # generic
        i = IntervalDtype(subtype)
        assert i.subtype is None
        assert is_interval_dtype(i)

    @pytest.mark.parametrize('subtype', [
        CategoricalDtype(list('abc'), False),
        CategoricalDtype(list('wxyz'), True),
        object, str, '<U10', 'interval[category]', 'interval[object]'])
    def test_construction_not_supported(self, subtype):
        # GH 19016
        msg = ('category, object, and string subtypes are not supported '
               'for IntervalDtype')
        with tm.assert_raises_regex(TypeError, msg):
            IntervalDtype(subtype)

    def test_construction_errors(self):
        msg = 'could not construct IntervalDtype'
        with tm.assert_raises_regex(ValueError, msg):
            IntervalDtype('xx')

    def test_construction_from_string(self):
        result = IntervalDtype('interval[int64]')
        assert is_dtype_equal(self.dtype, result)
        result = IntervalDtype.construct_from_string('interval[int64]')
        assert is_dtype_equal(self.dtype, result)

    @pytest.mark.parametrize('string', [
        'foo', 'interval[foo]', 'foo[int64]', 0, 3.14, ('a', 'b'), None])
    def test_construction_from_string_errors(self, string):
        if isinstance(string, string_types):
            error, msg = ValueError, 'could not construct IntervalDtype'
        else:
            error, msg = TypeError, 'a string needs to be passed, got type'

        with tm.assert_raises_regex(error, msg):
            IntervalDtype.construct_from_string(string)

    def test_subclass(self):
        a = IntervalDtype('interval[int64]')
        b = IntervalDtype('interval[int64]')

        assert issubclass(type(a), type(a))
        assert issubclass(type(a), type(b))

    def test_is_dtype(self):
        assert IntervalDtype.is_dtype(self.dtype)
        assert IntervalDtype.is_dtype('interval')
        assert IntervalDtype.is_dtype(IntervalDtype('float64'))
        assert IntervalDtype.is_dtype(IntervalDtype('int64'))
        assert IntervalDtype.is_dtype(IntervalDtype(np.int64))

        assert not IntervalDtype.is_dtype('D')
        assert not IntervalDtype.is_dtype('3D')
        assert not IntervalDtype.is_dtype('U')
        assert not IntervalDtype.is_dtype('S')
        assert not IntervalDtype.is_dtype('foo')
        assert not IntervalDtype.is_dtype(np.object_)
        assert not IntervalDtype.is_dtype(np.int64)
        assert not IntervalDtype.is_dtype(np.float64)

    def test_coerce_to_dtype(self):
        assert (_coerce_to_dtype('interval[int64]') ==
                IntervalDtype('interval[int64]'))

    def test_equality(self):
        assert is_dtype_equal(self.dtype, 'interval[int64]')
        assert is_dtype_equal(self.dtype, IntervalDtype('int64'))
        assert is_dtype_equal(IntervalDtype('int64'), IntervalDtype('int64'))

        assert not is_dtype_equal(self.dtype, 'int64')
        assert not is_dtype_equal(IntervalDtype('int64'),
                                  IntervalDtype('float64'))

        # invalid subtype comparisons do not raise when directly compared
        dtype1 = IntervalDtype('float64')
        dtype2 = IntervalDtype('datetime64[ns, US/Eastern]')
        assert dtype1 != dtype2
        assert dtype2 != dtype1

    @pytest.mark.parametrize('subtype', [
        None, 'interval', 'Interval', 'int64', 'uint64', 'float64',
        'complex128', 'datetime64', 'timedelta64', PeriodDtype('Q')])
    def test_equality_generic(self, subtype):
        # GH 18980
        dtype = IntervalDtype(subtype)
        assert is_dtype_equal(dtype, 'interval')
        assert is_dtype_equal(dtype, IntervalDtype())

    @pytest.mark.parametrize('subtype', [
        'int64', 'uint64', 'float64', 'complex128', 'datetime64',
        'timedelta64', PeriodDtype('Q')])
    def test_name_repr(self, subtype):
        # GH 18980
        dtype = IntervalDtype(subtype)
        expected = 'interval[{subtype}]'.format(subtype=subtype)
        assert str(dtype) == expected
        assert dtype.name == 'interval'

    @pytest.mark.parametrize('subtype', [None, 'interval', 'Interval'])
    def test_name_repr_generic(self, subtype):
        # GH 18980
        dtype = IntervalDtype(subtype)
        assert str(dtype) == 'interval'
        assert dtype.name == 'interval'

    def test_basic(self):
        assert is_interval_dtype(self.dtype)

        ii = IntervalIndex.from_breaks(range(3))

        assert is_interval_dtype(ii.dtype)
        assert is_interval_dtype(ii)

        s = Series(ii, name='A')

        # dtypes
        # series results in object dtype currently,
        assert not is_interval_dtype(s.dtype)
        assert not is_interval_dtype(s)

    def test_basic_dtype(self):
        assert is_interval_dtype('interval[int64]')
        assert is_interval_dtype(IntervalIndex.from_tuples([(0, 1)]))
        assert is_interval_dtype(IntervalIndex.from_breaks(np.arange(4)))
        assert is_interval_dtype(IntervalIndex.from_breaks(
            date_range('20130101', periods=3)))
        assert not is_interval_dtype('U')
        assert not is_interval_dtype('S')
        assert not is_interval_dtype('foo')
        assert not is_interval_dtype(np.object_)
        assert not is_interval_dtype(np.int64)
        assert not is_interval_dtype(np.float64)

    def test_caching(self):
        IntervalDtype.reset_cache()
        dtype = IntervalDtype("int64")
        assert len(IntervalDtype._cache) == 1

        IntervalDtype("interval")
        assert len(IntervalDtype._cache) == 2

        IntervalDtype.reset_cache()
        tm.round_trip_pickle(dtype)
        assert len(IntervalDtype._cache) == 0


class TestCategoricalDtypeParametrized(object):

    @pytest.mark.parametrize('categories, ordered', [
        (['a', 'b', 'c', 'd'], False),
        (['a', 'b', 'c', 'd'], True),
        (np.arange(1000), False),
        (np.arange(1000), True),
        (['a', 'b', 10, 2, 1.3, True], False),
        ([True, False], True),
        ([True, False], False),
        (pd.date_range('2017', periods=4), True),
        (pd.date_range('2017', periods=4), False),
    ])
    def test_basic(self, categories, ordered):
        c1 = CategoricalDtype(categories, ordered=ordered)
        tm.assert_index_equal(c1.categories, pd.Index(categories))
        assert c1.ordered is ordered

    def test_order_matters(self):
        categories = ['a', 'b']
        c1 = CategoricalDtype(categories, ordered=False)
        c2 = CategoricalDtype(categories, ordered=True)
        assert c1 is not c2

    def test_unordered_same(self):
        c1 = CategoricalDtype(['a', 'b'])
        c2 = CategoricalDtype(['b', 'a'])
        assert hash(c1) == hash(c2)

    def test_categories(self):
        result = CategoricalDtype(['a', 'b', 'c'])
        tm.assert_index_equal(result.categories, pd.Index(['a', 'b', 'c']))
        assert result.ordered is False

    def test_equal_but_different(self):
        c1 = CategoricalDtype([1, 2, 3])
        c2 = CategoricalDtype([1., 2., 3.])
        assert c1 is not c2
        assert c1 != c2

    @pytest.mark.parametrize('v1, v2', [
        ([1, 2, 3], [1, 2, 3]),
        ([1, 2, 3], [3, 2, 1]),
    ])
    def test_order_hashes_different(self, v1, v2):
        c1 = CategoricalDtype(v1)
        c2 = CategoricalDtype(v2, ordered=True)
        assert c1 is not c2

    def test_nan_invalid(self):
        with pytest.raises(ValueError):
            CategoricalDtype([1, 2, np.nan])

    def test_non_unique_invalid(self):
        with pytest.raises(ValueError):
            CategoricalDtype([1, 2, 1])

    def test_same_categories_different_order(self):
        c1 = CategoricalDtype(['a', 'b'], ordered=True)
        c2 = CategoricalDtype(['b', 'a'], ordered=True)
        assert c1 is not c2

    @pytest.mark.parametrize('ordered, other, expected', [
        (True, CategoricalDtype(['a', 'b'], True), True),
        (False, CategoricalDtype(['a', 'b'], False), True),
        (True, CategoricalDtype(['a', 'b'], False), False),
        (False, CategoricalDtype(['a', 'b'], True), False),
        (True, CategoricalDtype([1, 2], False), False),
        (False, CategoricalDtype([1, 2], True), False),
        (False, CategoricalDtype(None, True), True),
        (True, CategoricalDtype(None, True), True),
        (False, CategoricalDtype(None, False), True),
        (True, CategoricalDtype(None, False), True),
        (True, 'category', True),
        (False, 'category', True),
        (True, 'not a category', False),
        (False, 'not a category', False),
    ])
    def test_categorical_equality(self, ordered, other, expected):
        c1 = CategoricalDtype(['a', 'b'], ordered)
        result = c1 == other
        assert result == expected

    def test_invalid_raises(self):
        with tm.assert_raises_regex(TypeError, 'ordered'):
            CategoricalDtype(['a', 'b'], ordered='foo')

        with tm.assert_raises_regex(TypeError, 'collection'):
            CategoricalDtype('category')

    def test_mixed(self):
        a = CategoricalDtype(['a', 'b', 1, 2])
        b = CategoricalDtype(['a', 'b', '1', '2'])
        assert hash(a) != hash(b)

    def test_from_categorical_dtype_identity(self):
        c1 = Categorical([1, 2], categories=[1, 2, 3], ordered=True)
        # Identity test for no changes
        c2 = CategoricalDtype._from_categorical_dtype(c1)
        assert c2 is c1

    def test_from_categorical_dtype_categories(self):
        c1 = Categorical([1, 2], categories=[1, 2, 3], ordered=True)
        # override categories
        result = CategoricalDtype._from_categorical_dtype(
            c1, categories=[2, 3])
        assert result == CategoricalDtype([2, 3], ordered=True)

    def test_from_categorical_dtype_ordered(self):
        c1 = Categorical([1, 2], categories=[1, 2, 3], ordered=True)
        # override ordered
        result = CategoricalDtype._from_categorical_dtype(
            c1, ordered=False)
        assert result == CategoricalDtype([1, 2, 3], ordered=False)

    def test_from_categorical_dtype_both(self):
        c1 = Categorical([1, 2], categories=[1, 2, 3], ordered=True)
        # override ordered
        result = CategoricalDtype._from_categorical_dtype(
            c1, categories=[1, 2], ordered=False)
        assert result == CategoricalDtype([1, 2], ordered=False)

    def test_str_vs_repr(self):
        c1 = CategoricalDtype(['a', 'b'])
        assert str(c1) == 'category'
        # Py2 will have unicode prefixes
        pat = r"CategoricalDtype\(categories=\[.*\], ordered=False\)"
        assert re.match(pat, repr(c1))

    def test_categorical_categories(self):
        # GH17884
        c1 = CategoricalDtype(Categorical(['a', 'b']))
        tm.assert_index_equal(c1.categories, pd.Index(['a', 'b']))
        c1 = CategoricalDtype(CategoricalIndex(['a', 'b']))
        tm.assert_index_equal(c1.categories, pd.Index(['a', 'b']))


class DummyArray(ExtensionArray):
    pass


class DummyDtype(ExtensionDtype):
    pass


class TestExtensionArrayDtype(object):

    @pytest.mark.parametrize('values', [
        pd.Categorical([]),
        pd.Categorical([]).dtype,
        pd.Series(pd.Categorical([])),
        DummyDtype(),
        DummyArray(),
    ])
    def test_is_extension_array_dtype(self, values):
        assert is_extension_array_dtype(values)

    @pytest.mark.parametrize('values', [
        np.array([]),
        pd.Series(np.array([])),
    ])
    def test_is_not_extension_array_dtype(self, values):
        assert not is_extension_array_dtype(values)
