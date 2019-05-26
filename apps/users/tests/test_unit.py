from django.db import IntegrityError
from mock.mock import patch
from rest_framework.authtoken.models import Token

from apps.mixins import TestWrapper
from apps.users.models import User, Contact, Friend
from apps.users.tests.factories import UserFactory, ContactFactory, make_email, fake, PhoneNumberConfirmationFactory
from apps.users.tests.mock_functions import twilio_message_create


class TestUserModel(TestWrapper):
    user_factory = UserFactory
    contact_factory = ContactFactory

    def test_objects(self):
        users_count = 3
        contacts_count = 2
        self.user_factory.create_batch(users_count)
        self.contact_factory.create_batch(contacts_count)
        self.assertEqual(User.objects.count(), users_count)
        self.assertEqual(Contact.objects.count(), contacts_count)

    def test_facebook_field(self):
        fb_user = self.user_factory(fb_id='123')
        not_fb_user = self.user_factory()
        self.assertTrue(fb_user.is_facebook)
        self.assertFalse(not_fb_user.is_facebook)

    def test_get_token(self):
        user = self.user_factory()
        # there are no token
        self.assertFalse(Token.objects.filter(user=user).exists())
        token = user.get_token()
        self.assertEqual(token, Token.objects.get(user=user).key)

        # get existing token
        self.assertEqual(token, user.get_token())

        # token exists (must be recreated)
        self.assertNotEqual(token, user.get_token(recreate=True))

    def test_contact_user_field(self):
        contact = self.contact_factory()
        self.assertIsNone(contact.user)  # None because of User objects manager can't get Contact

    def test_contact_convert_to_user(self):
        contact = self.contact_factory()
        user = contact.convert_to_user()
        self.assertEqual(user.pk, contact.pk)
        self.assertTrue(User.objects.filter(pk=contact.pk).exists())
        self.assertFalse(Contact.objects.filter(pk=contact.pk).exists())

    def test_create_contacts(self):
        count = 5
        data = [{
            'email': make_email(),
            'first_name': fake.first_name(),
            'last_name': fake.last_name(),
        } for _ in range(count)]
        Contact.create_contacts(data)
        self.assertEqual(Contact.objects.count(), count)

    def test_create_contacts_if_user_exists(self):
        count = 5
        data = [{
            'email': make_email(),
            'first_name': fake.first_name(),
            'last_name': fake.last_name(),
        } for _ in range(count)]
        User.objects.create(email=data[0]['email'])  # become one to user
        Contact.create_contacts(data)
        self.assertEqual(Contact.objects.count(), count-1)

    def test_has_mutual(self):
        user = self.user_factory()
        friend = self.user_factory()
        self.assertFalse(user.has_mutual(friend))
        self.assertFalse(friend.has_mutual(user))

        user.subscriptions.create(related_user=friend)
        self.assertFalse(user.has_mutual(friend))
        self.assertFalse(friend.has_mutual(user))

        friend.subscriptions.create(related_user=user)
        self.assertTrue(user.has_mutual(friend))
        self.assertTrue(friend.has_mutual(user))


class TestFriendModel(TestWrapper):
    user_factory = UserFactory
    contact_factory = ContactFactory

    def test_objects(self):
        # objects manager returns friends relationships with User instances only (is_registered=True)
        user = self.user_factory()
        friend = self.user_factory()
        user.subscriptions.create(related_user=friend)
        self.assertEqual(user.subscriptions.count(), 1)

        contact_friend = self.contact_factory()
        user.subscriptions.create(related_user=contact_friend)
        self.assertEqual(user.subscriptions.count(), 1)  # still 1 because of this friend is a Contact instance

    def test_subscriptions(self):
        user = self.user_factory()
        friend = self.user_factory()
        self.assertEqual(user.subscriptions.count(), 0)
        self.assertEqual(friend.subscribers.count(), 0)
        user.subscriptions.create(related_user=friend)
        self.assertEqual(user.subscriptions.count(), 1)
        self.assertEqual(friend.subscribers.count(), 1)

    def test_subscriptions_with_contact(self):
        user = self.user_factory()
        contact_friend = self.contact_factory()
        self.assertEqual(user.subscriptions.count(), 0)  # user has no friends
        user.subscriptions.create(related_user=contact_friend)
        self.assertEqual(user.subscriptions.count(), 0)  # user still has no friends because of friend is a Contact
        friend = contact_friend.convert_to_user()
        self.assertEqual(user.subscriptions.count(), 1)  # now user has a friend becouse it was converted to User
        self.assertEqual(friend.subscribers.count(), 1)  # and reverse relationship too

    def test_impossibility_of_creating_identical_friends(self):
        user = self.user_factory()
        friend = self.user_factory()
        user.subscriptions.create(related_user=friend)
        self.assertEqual(Friend.objects.filter(user=user, related_user=friend).count(), 1)
        with self.assertRaises(IntegrityError):
            user.subscriptions.create(related_user=friend)

    def test_friends_creation_with_contact_creation(self):
        user = self.user_factory()
        count = 5
        data = [{
            'email': make_email(),
            'first_name': fake.first_name(),
            'last_name': fake.last_name(),
        } for _ in range(count)]
        Contact.create_contacts(data, user=user)
        self.assertEqual(Contact.objects.count(), count)
        self.assertEqual(Friend.objects.get_all().count(), count)

    def test_is_mutual(self):
        user = self.user_factory()
        friend = self.user_factory()
        friendship_direct = user.subscriptions.create(related_user=friend)
        # don't have mutual relationships
        self.assertFalse(friendship_direct.is_mutual())

        friendship_reverse = friend.subscriptions.create(related_user=user)
        # have mutual relationships
        self.assertTrue(friendship_direct.is_mutual())
        self.assertTrue(friendship_reverse.is_mutual())


class TestPhoneNumberConfirmation(TestWrapper):
    @patch('twilio.rest.api.v2010.account.message.MessageList.create', side_effect=twilio_message_create)
    def test_is_valid(self, mocked_function):
        o = PhoneNumberConfirmationFactory()
        assert True == o.is_valid(o.code)
        assert False == o.is_valid(1000)  # is not valid code

    @patch('twilio.rest.api.v2010.account.message.MessageList.create', side_effect=twilio_message_create)
    def test_save_to_user(self, mocked_function):
        user = UserFactory()
        o = PhoneNumberConfirmationFactory(user=user)
        o.save_to_user()
        o.refresh_from_db()
        user.refresh_from_db()
        assert True == o.is_confirmed
        assert user.phone_number == o.phone_number
