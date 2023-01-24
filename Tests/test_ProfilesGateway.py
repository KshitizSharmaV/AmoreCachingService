import pytest

from ProjectConf.FirestoreConf import async_db, db
from unittest.mock import patch, AsyncMock
from Tests.Utilities.test_base import async_mock_child
from Gateways.GeoserviceEXTs import GeoserviceGatewayEXT
from Gateways.ProfilesGateway import *

import asyncio
from unittest.mock import patch, MagicMock
import pytest

@pytest.mark.asyncio
async def test_ProfilesGateway_write_one_profile_to_cache_after_firebase_read_profile():
    # Arrange
    profile = {"id": "123", "name": "John Doe", "age": 30}
    profileDoc = MagicMock()
    profileDoc.to_dict.return_value = profile
    profileDoc.id = "123"
    profileDoc.exists = True
    with patch('Gateways.ProfilesGateway.async_db') as mock_db:
        mock_db.collection.return_value.document.return_value.get.side_effect = AsyncMock(return_value=profileDoc)
        with patch('Gateways.ProfilesGateway.GeoService_store_profiles') as mock_store_profiles:
            mock_store_profiles.return_value = asyncio.Future()
            
            # Act
            result = await ProfilesGateway_write_one_profile_to_cache_after_firebase_read(profileDoc.id)
            
            # Assert
            # mock_store_profiles.assert_called_once_with(profile=profile)
            assert result == profile
            

@pytest.mark.asyncio
async def test_ProfilesGateway_write_one_profile_to_cache_after_firebase_read_no_profile():
    # Arrange
    profile = None # No profile found
    profileDoc = MagicMock()
    profileDoc.to_dict.return_value = profile
    profileDoc.id = "123"
    profileDoc.exists = True
    with patch('Gateways.ProfilesGateway.async_db') as mock_db:
        mock_db.collection.return_value.document.return_value.get.side_effect = AsyncMock(return_value=profileDoc)
        with patch('Gateways.ProfilesGateway.GeoService_store_profiles') as mock_store_profiles:
            mock_store_profiles.return_value = asyncio.Future()
            
            # Act
            result = await ProfilesGateway_write_one_profile_to_cache_after_firebase_read(profileDoc.id)
            
            # Assert
            # mock_store_profiles.assert_called_once_with(profile=profile)
            assert result == None


@pytest.mark.asyncio
async def test_ProfilesGateway_write_one_profile_to_cache_after_firebase_read_failure():
    # Arrange
    profile = Exception("Raise an exception") # Raise an exception
    profileDoc = MagicMock()
    profileDoc.to_dict.return_value = profile
    profileDoc.id = "123"
    profileDoc.exists = True
    with patch('Gateways.ProfilesGateway.async_db') as mock_db:
        mock_db.collection.return_value.document.return_value.get.side_effect = AsyncMock(return_value=profileDoc)
        with patch('Gateways.ProfilesGateway.GeoService_store_profiles') as mock_store_profiles:
            mock_store_profiles.return_value = asyncio.Future()
            
            # Act
            result = await ProfilesGateway_write_one_profile_to_cache_after_firebase_read(profileDoc.id)
            
            # Assert
            # mock_store_profiles.assert_called_once_with(profile=profile)
            assert result == False

@pytest.mark.asyncio
async def test_ProfilesGateway_load_profiles_to_cache_from_firebase():
    # Arrange
    profileIdsNotInCache = ["123", "456"]
    profile1 = {"id": "123", "name": "John Doe", "age": 30}
    profile2 = {"id": "456", "name": "Jane Doe", "age": 28}
    profiles = [profile1, profile2]
    with patch('Gateways.ProfilesGateway.ProfilesGateway_write_one_profile_to_cache_after_firebase_read') as mock_write_profile:
        mock_write_profile.side_effect = AsyncMock(return_value=profiles)
        
        # Act
        result = await ProfilesGateway_load_profiles_to_cache_from_firebase(profileIdsNotInCache)

        # Assert
        assert mock_write_profile.call_count == 2
        print(mock_write_profile.call_args_list)
        assert result[0] == profiles


@pytest.mark.asyncio
async def test_ProfilesGateway_get_profile_by_ids_redis():
    """
    In following test case we load loading of profile from redis
    """
    # Arrange
    profileIdList = ["123"]
    profile1 = {"id": "123", "firstName": "John", "lastName":"Doe", "age": 30,'location': {}, 'image1': {}, 'image2': {}, 'image3': {}, 'image4': {}, 'image5': {}, 'image6': {}}
    profiles = [profile1]
    
    with patch('Gateways.ProfilesGateway.redis_client.hgetall') as mock_redis_hgetall:
        mock_redis_hgetall.return_value = Profile.encode_data_for_redis(profile1)
        with patch('Gateways.ProfilesGateway.ProfilesGateway_load_profiles_to_cache_from_firebase') as mock_load_profiles:
            # Act
            result = await ProfilesGateway_get_profile_by_ids(profileIdList)

            # Assert
            assert result == profiles


@pytest.mark.asyncio
async def test_ProfilesGateway_get_profile_by_ids_firestore():
    """
    In following test case we load loading of profile from firestore when there
    is no profile in redis
    """
    # Arrange
    profileIdList = ["123"]
    # Profile from redis has no id and it will fail the check 
    redis_profile = {"firstName": "John", "lastName":"Doe", "age": 30,'location': {}, 'image1': {}, 'image2': {}, 'image3': {}, 'image4': {}, 'image5': {}, 'image6': {}}
    firestore_profile = {"id": "123", "firstName": "John", "lastName":"Doe", "age": 30,'location': {}, 'image1': {}, 'image2': {}, 'image3': {}, 'image4': {}, 'image5': {}, 'image6': {}}
    
    with patch('Gateways.ProfilesGateway.redis_client.hgetall') as mock_redis_hgetall:
        mock_redis_hgetall.return_value = Profile.encode_data_for_redis(redis_profile)
        with patch('Gateways.ProfilesGateway.ProfilesGateway_load_profiles_to_cache_from_firebase') as mock_load_profiles:
            # Note* Always assign Async_Mock to side_effect
            mock_load_profiles.side_effect = AsyncMock(return_value=[firestore_profile])
            # Act
            result = await ProfilesGateway_get_profile_by_ids(profileIdList)
            # Assert
            assert result == [firestore_profile]
