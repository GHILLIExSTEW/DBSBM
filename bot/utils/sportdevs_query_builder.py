"""
SportDevs Query Builder
Implements the SportDevs endpoint query syntax for building API requests.
"""

from typing import List, Optional, Union, Callable
from urllib.parse import urlencode


class SportDevsOrderBuilder:
    """Builder for SportDevs order clauses."""
    
    def __init__(self):
        self.order_parts = []
    
    def order_property(self, name: str) -> 'SportDevsOrderBuilder':
        """Set the property to order by."""
        self.current_property = name
        return self
    
    @property
    def ascending(self) -> 'SportDevsOrderBuilder':
        """Set ascending order."""
        if hasattr(self, 'current_property'):
            self.order_parts.append(f"{self.current_property}.asc")
        return self
    
    @property
    def descending(self) -> 'SportDevsOrderBuilder':
        """Set descending order."""
        if hasattr(self, 'current_property'):
            self.order_parts.append(f"{self.current_property}.desc")
        return self
    
    @property
    def nullsFirst(self) -> 'SportDevsOrderBuilder':
        """Add nulls first to the current order."""
        if self.order_parts:
            self.order_parts[-1] += ".nullsfirst"
        return self
    
    @property
    def nullsLast(self) -> 'SportDevsOrderBuilder':
        """Add nulls last to the current order."""
        if self.order_parts:
            self.order_parts[-1] += ".nullslast"
        return self
    
    def get_order_string(self) -> str:
        """Get the order string."""
        return ",".join(self.order_parts)


class SportDevsQueryBuilder:
    """Builder for SportDevs API queries using their specific syntax."""
    
    def __init__(self, endpoint: str):
        self.endpoint = endpoint
        self.params = {}
        self._current_property = None
        self._current_operator = None
        self._current_value = None
        self._logical_group = None
    
    def property(self, name: str) -> 'SportDevsQueryBuilder':
        """Set the current property for filtering."""
        self._current_property = name
        return self
    
    def equals(self, value: Union[str, int, float]) -> 'SportDevsQueryBuilder':
        """Add equals filter: property=eq.value"""
        if self._current_property:
            self.params[self._current_property] = f"eq.{value}"
        return self
    
    def greater_than(self, value: Union[str, int, float]) -> 'SportDevsQueryBuilder':
        """Add greater than filter: property=gt.value"""
        if self._current_property:
            self.params[self._current_property] = f"gt.{value}"
        return self
    
    def greater_than_or_equal(self, value: Union[str, int, float]) -> 'SportDevsQueryBuilder':
        """Add greater than or equal filter: property=gte.value"""
        if self._current_property:
            self.params[self._current_property] = f"gte.{value}"
        return self
    
    def less_than(self, value: Union[str, int, float]) -> 'SportDevsQueryBuilder':
        """Add less than filter: property=lt.value"""
        if self._current_property:
            self.params[self._current_property] = f"lt.{value}"
        return self
    
    def less_than_or_equal(self, value: Union[str, int, float]) -> 'SportDevsQueryBuilder':
        """Add less than or equal filter: property=lte.value"""
        if self._current_property:
            self.params[self._current_property] = f"lte.{value}"
        return self
    
    def like(self, pattern: str) -> 'SportDevsQueryBuilder':
        """Add like filter: property=like.pattern"""
        if self._current_property:
            self.params[self._current_property] = f"like.{pattern}"
        return self
    
    def insensitive_like(self, pattern: str) -> 'SportDevsQueryBuilder':
        """Add case-insensitive like filter: property=ilike.pattern"""
        if self._current_property:
            self.params[self._current_property] = f"ilike.{pattern}"
        return self
    
    def match(self, pattern: str) -> 'SportDevsQueryBuilder':
        """Add regex match filter: property=match.pattern"""
        if self._current_property:
            self.params[self._current_property] = f"match.{pattern}"
        return self
    
    def insensitive_match(self, pattern: str) -> 'SportDevsQueryBuilder':
        """Add case-insensitive regex match filter: property=imatch.pattern"""
        if self._current_property:
            self.params[self._current_property] = f"imatch.{pattern}"
        return self
    
    def in_values(self, *values: Union[str, int, float]) -> 'SportDevsQueryBuilder':
        """Add in filter: property=in.(value1,value2,value3)"""
        if self._current_property:
            values_str = ",".join(str(v) for v in values)
            self.params[self._current_property] = f"in.({values_str})"
        return self
    
    def is_null(self) -> 'SportDevsQueryBuilder':
        """Add is null filter: property=is.null"""
        if self._current_property:
            self.params[self._current_property] = "is.null"
        return self
    
    def is_not_null(self) -> 'SportDevsQueryBuilder':
        """Add is not null filter: property=not.is.null"""
        if self._current_property:
            self.params[self._current_property] = "not.is.null"
        return self
    
    def not_equals(self, value: Union[str, int, float]) -> 'SportDevsQueryBuilder':
        """Add not equals filter: property=not.eq.value"""
        if self._current_property:
            self.params[self._current_property] = f"not.eq.{value}"
        return self
    
    def not_greater_than(self, value: Union[str, int, float]) -> 'SportDevsQueryBuilder':
        """Add not greater than filter: property=not.gt.value"""
        if self._current_property:
            self.params[self._current_property] = f"not.gt.{value}"
        return self
    
    def not_less_than(self, value: Union[str, int, float]) -> 'SportDevsQueryBuilder':
        """Add not less than filter: property=not.lt.value"""
        if self._current_property:
            self.params[self._current_property] = f"not.lt.{value}"
        return self
    
    def offset(self, value: int) -> 'SportDevsQueryBuilder':
        """Add offset parameter."""
        self.params['offset'] = value
        return self
    
    def limit(self, value: int) -> 'SportDevsQueryBuilder':
        """Add limit parameter."""
        self.params['limit'] = value
        return self
    
    def select(self, *properties: str) -> 'SportDevsQueryBuilder':
        """Add select parameter."""
        self.params['select'] = ",".join(properties)
        return self
    
    def order(self, order_func: Callable[['SportDevsOrderBuilder'], 'SportDevsOrderBuilder']) -> 'SportDevsQueryBuilder':
        """Add order parameter using a function."""
        order_builder = SportDevsOrderBuilder()
        order_func(order_builder)
        self.params['order'] = order_builder.get_order_string()
        return self
    
    def order_asc(self, property_name: str) -> 'SportDevsQueryBuilder':
        """Add ascending order parameter."""
        self.params['order'] = f"{property_name}.asc"
        return self
    
    def order_desc(self, property_name: str) -> 'SportDevsQueryBuilder':
        """Add descending order parameter."""
        self.params['order'] = f"{property_name}.desc"
        return self
    
    def and_filter(self, filter_func: Callable[['SportDevsQueryBuilder'], 'SportDevsQueryBuilder']) -> 'SportDevsQueryBuilder':
        """Add AND logical filter."""
        # Create a temporary builder for the AND group
        temp_builder = SportDevsQueryBuilder(self.endpoint)
        filter_func(temp_builder)
        
        # Combine the conditions with AND
        conditions = []
        for key, value in temp_builder.params.items():
            if key not in ['offset', 'limit', 'select', 'order']:
                conditions.append(f"{key}.{value}")
        
        if conditions:
            self.params['and'] = f"({','.join(conditions)})"
        
        return self
    
    def or_filter(self, filter_func: Callable[['SportDevsQueryBuilder'], 'SportDevsQueryBuilder']) -> 'SportDevsQueryBuilder':
        """Add OR logical filter."""
        # Create a temporary builder for the OR group
        temp_builder = SportDevsQueryBuilder(self.endpoint)
        filter_func(temp_builder)
        
        # Combine the conditions with OR
        conditions = []
        for key, value in temp_builder.params.items():
            if key not in ['offset', 'limit', 'select', 'order']:
                conditions.append(f"{key}.{value}")
        
        if conditions:
            self.params['or'] = f"({','.join(conditions)})"
        
        return self
    
    def and_(self, filter_func: Callable[['SportDevsQueryBuilder'], 'SportDevsQueryBuilder']) -> 'SportDevsQueryBuilder':
        """Add AND logical filter (alias for and_filter)."""
        return self.and_filter(filter_func)
    
    def or_(self, filter_func: Callable[['SportDevsQueryBuilder'], 'SportDevsQueryBuilder']) -> 'SportDevsQueryBuilder':
        """Add OR logical filter (alias for or_filter)."""
        return self.or_filter(filter_func)
    
    def not_and(self, filter_func: Callable[['SportDevsQueryBuilder'], 'SportDevsQueryBuilder']) -> 'SportDevsQueryBuilder':
        """Add NOT AND logical filter."""
        # Create a temporary builder for the AND group
        temp_builder = SportDevsQueryBuilder(self.endpoint)
        filter_func(temp_builder)
        
        # Combine the conditions with AND and add NOT prefix
        conditions = []
        for key, value in temp_builder.params.items():
            if key not in ['offset', 'limit', 'select', 'order']:
                conditions.append(f"{key}.{value}")
        
        if conditions:
            self.params['not.and'] = f"({','.join(conditions)})"
        
        return self
    
    def not_or(self, filter_func: Callable[['SportDevsQueryBuilder'], 'SportDevsQueryBuilder']) -> 'SportDevsQueryBuilder':
        """Add NOT OR logical filter."""
        # Create a temporary builder for the OR group
        temp_builder = SportDevsQueryBuilder(self.endpoint)
        filter_func(temp_builder)
        
        # Combine the conditions with OR and add NOT prefix
        conditions = []
        for key, value in temp_builder.params.items():
            if key not in ['offset', 'limit', 'select', 'order']:
                conditions.append(f"{key}.{value}")
        
        if conditions:
            self.params['not.or'] = f"({','.join(conditions)})"
        
        return self
    
    def build_url(self) -> str:
        """Build the complete URL with query parameters."""
        if self.params:
            query_string = urlencode(self.params, doseq=True)
            return f"{self.endpoint}?{query_string}"
        return self.endpoint
    
    def __str__(self) -> str:
        """Return the built URL as a string."""
        return self.build_url()
    
    def toString(self) -> str:
        """Return the built URL as a string (alias for __str__)."""
        return self.build_url()
    
    def get_params(self) -> dict:
        """Get the current parameters dictionary."""
        return self.params.copy()


def endpoint(name: str) -> SportDevsQueryBuilder:
    """Create a new SportDevs query builder for the given endpoint."""
    return SportDevsQueryBuilder(name)


# Example usage functions for common queries
def get_matches_by_date(date: str, limit: int = 50) -> str:
    """Get matches for a specific date."""
    return endpoint("matches").property("date").equals(date).limit(limit).build_url()


def get_matches_by_season(season_id: int, limit: int = 50) -> str:
    """Get matches for a specific season."""
    return endpoint("matches").property("season_id").equals(season_id).limit(limit).build_url()


def get_matches_by_tournament(tournament_id: int, limit: int = 50) -> str:
    """Get matches for a specific tournament."""
    return endpoint("matches").property("tournament_id").equals(tournament_id).limit(limit).build_url()


def get_tournaments(limit: int = 50) -> str:
    """Get all tournaments."""
    return endpoint("tournaments").limit(limit).build_url()


def get_seasons(limit: int = 50) -> str:
    """Get all seasons."""
    return endpoint("seasons").limit(limit).build_url()


def get_teams(limit: int = 50) -> str:
    """Get all teams."""
    return endpoint("teams").limit(limit).build_url()


def get_players(limit: int = 50) -> str:
    """Get all players."""
    return endpoint("players").limit(limit).build_url() 