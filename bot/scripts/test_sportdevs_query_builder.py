#!/usr/bin/env python3
"""
Test script to verify SportDevs query builder matches official documentation.
"""

import sys
import os

# Add the bot directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.sportdevs_query_builder import endpoint, SportDevsQueryBuilder

def test_documentation_examples():
    """Test the examples from the SportDevs documentation."""
    
    print("Testing SportDevs Query Builder against official documentation...")
    print("=" * 60)
    
    # Test 1: Basic endpoint creation
    print("\n1. Basic endpoint creation:")
    query = endpoint("matches")
    print(f"   endpoint('matches') -> {query}")
    
    # Test 2: toString() method
    print("\n2. toString() method:")
    query = endpoint("matches").toString()
    print(f"   endpoint('matches').toString() -> {query}")
    
    # Test 3: Response transforms
    print("\n3. Response transforms:")
    
    # offset
    query = endpoint("matches").offset(1)
    print(f"   endpoint('matches').offset(1) -> {query}")
    
    # limit
    query = endpoint("matches").limit(1)
    print(f"   endpoint('matches').limit(1) -> {query}")
    
    # select
    query = endpoint("matches").select("home_team_id", "away_team_id")
    print(f"   endpoint('matches').select('home_team_id', 'away_team_id') -> {query}")
    
    # Test 4: Property transforms
    print("\n4. Property transforms:")
    
    # equals
    query = endpoint("matches").property("id").equals(10)
    print(f"   endpoint('matches').property('id').equals(10) -> {query}")
    
    # greaterThan
    query = endpoint("matches").property("id").greater_than(10)
    print(f"   endpoint('matches').property('id').greaterThan(10) -> {query}")
    
    # lessThan
    query = endpoint("matches").property("id").less_than(10)
    print(f"   endpoint('matches').property('id').lessThan(10) -> {query}")
    
    # like
    query = endpoint("players").property("first_name").like("A*")
    print(f"   endpoint('players').property('first_name').like('A*') -> {query}")
    
    # insensitive like
    query = endpoint("players").property("first_name").insensitive_like("A*")
    print(f"   endpoint('players').property('first_name').insensitive.like('A*') -> {query}")
    
    # match
    query = endpoint("players").property("first_name").match("^A")
    print(f"   endpoint('players').property('first_name').match('^A') -> {query}")
    
    # in
    query = endpoint("matches").property("id").in_values(1, 2, 3)
    print(f"   endpoint('matches').property('id').in(1, 2, 3) -> {query}")
    
    # is null
    query = endpoint("matches").property("id").is_null()
    print(f"   endpoint('matches').property('id').is('null') -> {query}")
    
    # Test 5: Negated property transforms
    print("\n5. Negated property transforms:")
    
    # not equals
    query = endpoint("matches").property("id").not_equals(10)
    print(f"   endpoint('matches').property('id').not.equals(10) -> {query}")
    
    # not lessThan
    query = endpoint("matches").property("id").not_less_than(10)
    print(f"   endpoint('matches').property('id').not.lessThan(10) -> {query}")
    
    # Test 6: Logical transforms
    print("\n6. Logical transforms:")
    
    # and
    query = endpoint("matches").and_filter(lambda obj: 
        obj.property("id").less_than(10).property("id").not_equals(1)
    )
    print(f"   endpoint('matches').and((obj) => obj.property('id').lessThan(10).property('id').not.equals(1)) -> {query}")
    
    # or
    query = endpoint("matches").or_filter(lambda obj: 
        obj.property("id").less_than(10).property("id").not_equals(1)
    )
    print(f"   endpoint('matches').or((obj) => obj.property('id').lessThan(10).property('id').not.equals(1)) -> {query}")
    
    # Test 7: Sort transforms
    print("\n7. Sort transforms:")
    
    # order ascending
    query = endpoint("matches").order(lambda obj: obj.property("id").ascending)
    print(f"   endpoint('matches').order((obj) => obj.property('id').ascending) -> {query}")
    
    # order descending
    query = endpoint("matches").order(lambda obj: obj.property("id").descending)
    print(f"   endpoint('matches').order((obj) => obj.property('id').descending) -> {query}")
    
    # order with nullsFirst
    query = endpoint("matches").order(lambda obj: obj.property("id").ascending.nullsFirst)
    print(f"   endpoint('matches').order((obj) => obj.property('id').ascending.nullsFirst) -> {query}")
    
    # order with nullsLast
    query = endpoint("matches").order(lambda obj: obj.property("id").descending.nullsLast)
    print(f"   endpoint('matches').order((obj) => obj.property('id').descending.nullsLast) -> {query}")
    
    # Test 8: Complex example from documentation
    print("\n8. Complex example from documentation:")
    query = endpoint("matches").property("season_id").equals(18820).or_filter(lambda obj:
        obj.property("away_team_score->current").greater_than(3).property("home_team_score->current").greater_than(3)
    ).select("away_team_id", "home_team_id", "away_team_score", "home_team_score").order(lambda obj: obj.property("id").descending)
    print(f"   Complex query -> {query}")
    
    # Expected: matches?season_id=eq.18820&or=(away_team_score->current.gt.3,home_team_score->current.gt.3)&select=away_team_id,home_team_id,away_team_score,home_team_score&order=id.desc
    print(f"   Expected: matches?season_id=eq.18820&or=(away_team_score->current.gt.3,home_team_score->current.gt.3)&select=away_team_id,home_team_id,away_team_score,home_team_score&order=id.desc")
    
    print("\n" + "=" * 60)
    print("Query builder test completed!")

if __name__ == "__main__":
    test_documentation_examples() 