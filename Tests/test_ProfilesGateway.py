import pytest
from ProjectConf.FirestoreConf import async_db, db
from unittest.mock import patch, AsyncMock
from Tests.Utilities.test_base import async_mock_child
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
        with patch('Gateways.ProfilesGateway.Profiles_store_profiles') as mock_store_profiles:
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
        with patch('Gateways.ProfilesGateway.Profiles_store_profiles') as mock_store_profiles:
            mock_store_profiles.return_value = await async_mock_child(return_value=True)
            
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
        with patch('Gateways.ProfilesGateway.Profiles_store_profiles') as mock_store_profiles:
            mock_store_profiles.return_value = await async_mock_child(return_value=True)
            
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
    profile_id_list = ['UserId123']
    profile = {'id':'UserId123','firstName':'TestName'}
    with patch('Gateways.ProfilesGateway.redis_client') as mock_redis_client:
        mock_redis_client.get.return_value = profile
        with patch('Gateways.ProfilesGateway.serialise_deserialise_date_in_profile') as mock_serialise_deserialise_date_in_profile:
            mock_serialise_deserialise_date_in_profile.return_value = profile
            result = await ProfilesGateway_get_profile_by_ids(profileIdList=profile_id_list)
            assert result == [profile]