import pytest


class TestGetActivities:
    """Tests for the GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) == 7
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
        assert "Basketball Team" in data
        assert "Tennis Club" in data
        assert "Drama Club" in data
        assert "Art Studio" in data
    
    def test_activity_has_required_fields(self, client, reset_activities):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)
    
    def test_participants_list_content(self, client, reset_activities):
        """Test that participants are correctly loaded"""
        response = client.get("/activities")
        data = response.json()
        
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
        assert "emma@mergington.edu" in data["Programming Class"]["participants"]
        assert "john@mergington.edu" in data["Gym Class"]["participants"]


class TestSignupForActivity:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_new_participant(self, client, reset_activities):
        """Test signing up a new participant to an activity"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]
    
    def test_signup_adds_participant_to_activity(self, client, reset_activities):
        """Test that signup actually adds participant to the activity"""
        client.post(
            "/activities/Chess%20Club/signup?email=newstudent@mergington.edu"
        )
        
        # Get activities and verify participant was added
        response = client.get("/activities")
        data = response.json()
        assert "newstudent@mergington.edu" in data["Chess Club"]["participants"]
    
    def test_signup_duplicate_participant_fails(self, client, reset_activities):
        """Test that signing up an already registered participant fails"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
        assert "already signed up" in data["detail"]
    
    def test_signup_nonexistent_activity_fails(self, client, reset_activities):
        """Test that signing up for a nonexistent activity fails"""
        response = client.post(
            "/activities/NonExistent%20Activity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"]
    
    def test_signup_multiple_participants(self, client, reset_activities):
        """Test signing up multiple different participants"""
        emails = [
            "student1@mergington.edu",
            "student2@mergington.edu",
            "student3@mergington.edu"
        ]
        
        for email in emails:
            response = client.post(
                f"/activities/Tennis%20Club/signup?email={email}"
            )
            assert response.status_code == 200
        
        # Verify all were added
        response = client.get("/activities")
        data = response.json()
        for email in emails:
            assert email in data["Tennis Club"]["participants"]


class TestUnregisterFromActivity:
    """Tests for the DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_existing_participant(self, client, reset_activities):
        """Test unregistering an existing participant"""
        response = client.delete(
            "/activities/Chess%20Club/unregister?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "michael@mergington.edu" in data["message"]
    
    def test_unregister_removes_participant(self, client, reset_activities):
        """Test that unregister actually removes participant from activity"""
        client.delete(
            "/activities/Chess%20Club/unregister?email=michael@mergington.edu"
        )
        
        # Get activities and verify participant was removed
        response = client.get("/activities")
        data = response.json()
        assert "michael@mergington.edu" not in data["Chess Club"]["participants"]
    
    def test_unregister_nonexistent_participant_fails(self, client, reset_activities):
        """Test that unregistering a participant not in the activity fails"""
        response = client.delete(
            "/activities/Chess%20Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
        assert "not signed up" in data["detail"]
    
    def test_unregister_nonexistent_activity_fails(self, client, reset_activities):
        """Test that unregistering from a nonexistent activity fails"""
        response = client.delete(
            "/activities/NonExistent%20Activity/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"]
    
    def test_unregister_multiple_participants(self, client, reset_activities):
        """Test unregistering multiple participants"""
        # First, sign up some participants
        emails = ["student1@mergington.edu", "student2@mergington.edu"]
        for email in emails:
            client.post(f"/activities/Tennis%20Club/signup?email={email}")
        
        # Now unregister them
        for email in emails:
            response = client.delete(
                f"/activities/Tennis%20Club/unregister?email={email}"
            )
            assert response.status_code == 200
        
        # Verify they were removed
        response = client.get("/activities")
        data = response.json()
        for email in emails:
            assert email not in data["Tennis Club"]["participants"]


class TestIntegration:
    """Integration tests for signup and unregister workflows"""
    
    def test_signup_then_unregister_workflow(self, client, reset_activities):
        """Test complete workflow: signup, verify, unregister, verify"""
        email = "integrationtest@mergington.edu"
        activity = "Drama%20Club"
        
        # Signup
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200
        
        # Verify participant was added
        response = client.get("/activities")
        data = response.json()
        assert email in data["Drama Club"]["participants"]
        
        # Unregister
        response = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert response.status_code == 200
        
        # Verify participant was removed
        response = client.get("/activities")
        data = response.json()
        assert email not in data["Drama Club"]["participants"]
    
    def test_cannot_signup_same_participant_twice(self, client, reset_activities):
        """Test that signing up the same participant twice fails on second attempt"""
        email = "doubletest@mergington.edu"
        activity = "Art%20Studio"
        
        # First signup should succeed
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200
        
        # Second signup should fail
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 400
    
    def test_participant_count_accuracy(self, client, reset_activities):
        """Test that participant counts are accurate after operations"""
        activity_name = "Programming Class"
        
        # Get initial count
        response = client.get("/activities")
        initial_data = response.json()
        initial_count = len(initial_data[activity_name]["participants"])
        
        # Add a participant
        client.post(
            f"/activities/Programming%20Class/signup?email=newprog@mergington.edu"
        )
        
        # Verify count increased
        response = client.get("/activities")
        data = response.json()
        assert len(data[activity_name]["participants"]) == initial_count + 1
        
        # Remove a participant
        client.delete(
            f"/activities/Programming%20Class/unregister?email=newprog@mergington.edu"
        )
        
        # Verify count is back to initial
        response = client.get("/activities")
        data = response.json()
        assert len(data[activity_name]["participants"]) == initial_count
