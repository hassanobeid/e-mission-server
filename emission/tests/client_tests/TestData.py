# Standard imports
import unittest
import json
import logging
from datetime import datetime, timedelta

# Our imports
from emission.core.get_database import get_db, get_mode_db, get_section_db
from emission.core.wrapper.user import User
import emission.tests.common
from emission.clients.data import data

import emission.tests.common as etc

class TestDefault(unittest.TestCase):
    def setUp(self):
        # Sometimes, we may have entries left behind in the database if one of the tests failed
        # or threw an exception, so let us start by cleaning up all entries
        emission.tests.common.dropAllCollections(get_db())
        user = User.register("fake@fake.com")
        self.uuid = user.uuid
        self.serverName = "localhost"
        self.now = datetime.now()
        self.dayago = self.now - timedelta(days=1)
        self.weekago = self.now - timedelta(weeks = 1)

    def testCarbonFootprintStore(self):
        user = User.fromUUID(self.uuid)
        # Tuple of JSON objects, similar to the real footprint
        dummyCarbonFootprint = ({'myModeShareCount': 10}, {'avgModeShareCount': 20})
        self.assertEquals(data.getCarbonFootprint(user), None)
        data.setCarbonFootprint(user, dummyCarbonFootprint)
        # recall that pymongo converts tuples to lists somewhere down the line
        self.assertEquals(data.getCarbonFootprint(user), list(dummyCarbonFootprint))
    
    def testGetCategorySum(self):
        calcSum = data.getCategorySum({'walking': 1, 'cycling': 2, 'bus': 3, 'train': 4, 'car': 5})
        self.assertEqual(calcSum, 15)

    def testRunBackgroundTasksForDay(self):
        self.testUsers = ["test@example.com", "best@example.com", "fest@example.com",
                          "rest@example.com", "nest@example.com"]
        emission.tests.common.loadTable(self.serverName, "Stage_Modes", "emission/tests/data/modes.json")
        emission.tests.common.loadTable(self.serverName, "Stage_Sections", "emission/tests/data/testCarbonFile")

        # Let's make sure that the users are registered so that they have profiles
        for userEmail in self.testUsers:
          User.register(userEmail)

        self.SectionsColl = get_section_db()
        emission.tests.common.updateSections(self)

        self.assertNotEqual(len(self.uuid_list), 0)
        # Can access the zeroth element because we know that then length is greater than zero
        # (see above)
        test_uuid = self.uuid_list[0]
        test_user = User.fromUUID(test_uuid)
        self.assertNotIn('carbon_footprint', test_user.getProfile().keys())
        data.runBackgroundTasks(test_user.uuid)
        self.assertIn('carbon_footprint', test_user.getProfile().keys())

if __name__ == '__main__':
    etc.configLogging()
    unittest.main()
