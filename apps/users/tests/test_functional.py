import io

from PIL import Image
from django.urls import reverse
from mock.mock import patch
from rest_framework.authtoken.models import Token

from apps.gamification.level_templates import get_next_level_points
from apps.users.models import User, PhoneNumberConfirmation
from apps.mixins import TestWrapper
from apps.users.tests import factories
from apps.users.tests.factories import ContactFactory
from apps.users.tests.mock_functions import twilio_message_create


class CustomTestWrapper(TestWrapper):
    def setUp(self):
        super().setUp()
        self.user = factories.UserFactory()
        self.admin = factories.AdminFactory()
        self.another_user = factories.UserFactory()
        self.login(self.user)


class AuthTest(TestWrapper):
    def setUp(self):
        super().setUp()

        self.user = factories.UserFactory()
        Token.objects.get_or_create(user=self.user)

        self.admin = factories.AdminFactory()
        Token.objects.get_or_create(user=self.admin)

        # urls
        self.signin_url = reverse('signin')
        self.signout_url = reverse('auth-signout')
        self.signup_url = reverse('auth-signup')

    def test_login(self):
        self.logout()
        data = {
            'email': self.user.email,
            'password': factories.DEFAULT_PASSWORD,
        }
        response = self.client.post(self.signin_url, data)
        self.assertStatus200(response)
        token = response.data.get('token')
        self.assertTrue(Token.objects.filter(key=token).exists())

    def test_login_with_wrong_password(self):
        self.logout()
        data = {
            'email': self.user.email,
            'password': factories.WRONG_PASSWORD,
        }
        response = self.client.post(self.signin_url, **data)
        self.assertStatus400(response)

    def test_login_without_required_fields(self):
        self.logout()
        data = {
            'email': self.user.email,
        }
        response = self.client.post(self.signin_url, **data)
        self.assertStatus400(response)

        data = {
            'password': factories.DEFAULT_PASSWORD,
        }
        response = self.client.post(self.signin_url, **data)
        self.assertStatus400(response)

    def test_saving_token_for_multiple_devices(self):
        self.logout()
        data = {
            'email': self.user.email,
            'password': factories.DEFAULT_PASSWORD,
        }
        response = self.client.post(self.signin_url, data)
        prev_token = response.data.get('token')
        for i in range(3):
            response = self.client.post(self.signin_url, data)
            self.assertStatus200(response)
            token = response.data.get('token')
            self.assertEqual(prev_token, token)

    def test_logout(self):
        self.login(self.user)
        response = self.client.post(self.signout_url)
        self.assertStatus200(response)
        self.assertFalse(Token.objects.filter(user=self.user).exists())

    def test_registration(self):
        self.logout()
        data = {
            'email': factories.make_email(),
            'password': factories.DEFAULT_PASSWORD,
        }
        response = self.client.post(self.signup_url, data, format='json')
        self.assertStatus201(response)
        user = User.objects.get(pk=response.data.get('id'))
        self.assertFields(response, user, ['email', ])

    def test_registration_without_required_fields(self):
        self.logout()
        data = {
            'password': factories.DEFAULT_PASSWORD,
        }
        response = self.client.post(self.signup_url, data, format='json')
        self.assertStatus400(response)
        self.assertFieldError(response, 'email', 'This field is required.')

        data = {
            'email': factories.make_email(),
        }
        response = self.client.post(self.signup_url, data, format='json')
        self.assertStatus400(response)
        self.assertFieldError(response, 'password', 'This field is required.')

    def test_registration_if_user_exists(self):
        self.logout()
        data = {
            'email': self.user.email,
            'password': factories.DEFAULT_PASSWORD,
        }
        response = self.client.post(self.signup_url, data, format='json')
        self.assertStatus400(response)
        self.assertFieldError(response, 'email', 'user with this Email address already exists.')

    def test_registration_if_user_is_banned(self):
        self.logout()
        banned_user = factories.BannedUserFactory()
        data = {
            'email': banned_user.email,
            'password': factories.DEFAULT_PASSWORD,
        }
        response = self.client.post(self.signup_url, data, format='json')
        self.assertStatus400(response)
        self.assertFieldError(response, 'email', 'user with this Email address already exists.')

    def test_registration_if_contact_exists(self):
        self.logout()
        data = {
            'email': factories.make_email(),
            'password': factories.DEFAULT_PASSWORD,
        }
        ContactFactory(email=data['email'])
        response = self.client.post(self.signup_url, data, format='json')
        self.assertStatus201(response)
        user = User.objects.get(pk=response.data.get('id'))
        self.assertFields(response, user, ['email', ])


class UsersTest(CustomTestWrapper):
    base_name = 'users'
    factory = factories.UserFactory

    def get_temp_image(self, width=200, height=200):
        file = io.BytesIO()
        image = Image.new('RGB', size=(width, height), color=(155, 0, 0))
        image.save(file, 'png')
        file.name = 'some.png'
        file.seek(0)
        return file

    def test_list(self):
        # must returns the friends only
        count = 3
        friends = self.factory.create_batch(count)
        for friend in friends:
            self.user.subscriptions.create(related_user=friend)
        response = self.list()
        self.assertStatus200(response)
        self.assertEqual(len(self.data), count)
        ids = [x['id'] for x in self.data]
        for friend in friends:
            self.assertIn(friend.pk, ids)

    def test_retrieve(self):
        response = self.retrieve(self.user)
        self.assertStatus200(response)
        gamification = self.data.get('gamification')
        self.assertEqual(gamification['points'], self.user.score.points)
        self.assertEqual(gamification['level'], self.user.score.level)
        self.assertEqual(gamification['next_level_points'], get_next_level_points(self.user.score.level))
        self.assertFields(response, self.user, ['id', 'email', 'phone_number', 'username', 'first_name', 'last_name'])

    def test_retrieve_access(self):
        response = self.retrieve(self.another_user)
        self.assertStatus404(response)

    def test_retrieve_friend(self):
        friend = self.factory()
        self.user.subscriptions.create(related_user=friend)
        response = self.retrieve(friend)
        self.assertStatus200(response)
        self.assertFields(response, friend, ['id', 'email', 'phone_number', 'username', 'first_name', 'last_name'])

    def test_retrieve_access_as_guest(self):
        self.logout()
        self.assertStatus401(
            self.retrieve(self.another_user)
        )

    def test_retrieve_nonexistent_object(self):
        self.assertStatus404(
            self.retrieve(1000000)
        )

    def test_update(self):
        data = {
            'first_name': 'new-name',
            'last_name': 'new-name',
        }
        response = self.partial_update(self.user, data=data)
        self.assertStatus200(response)
        user = User.objects.get(pk=self.user.pk)
        self.assertFieldsDict(user, data, ['first_name', 'last_name', ])

    def test_update_access(self):
        data = {
            'first_name': 'new-name',
            'last_name': 'new-name',
        }
        self.assertStatus404(
            self.partial_update(self.another_user, **data)
        )

    def test_update_friend(self):
        friend = self.factory()
        self.user.subscriptions.create(related_user=friend)
        data = {
            'first_name': 'new-name',
            'last_name': 'new-name',
        }
        self.assertStatus404(
            self.partial_update(friend, **data)
        )

    def test_update_access_as_guest(self):
        self.logout()
        data = {
            'first_name': 'new-name',
            'last_name': 'new-name',
        }
        self.assertStatus401(
            self.partial_update(self.user, **data)
        )

    def test_update_with_picture(self):
        self.assertFalse(bool(self.user.picture))
        data = {
            'first_name': 'new-name',
            'picture': self.get_temp_image(),
        }
        self.assertStatus200(
            self.partial_update(self.user, data=data, format='multipart')
        )
        user = User.objects.get(pk=self.user.pk)
        self.assertFieldsDict(user, data, ['first_name', ])
        self.assertTrue(bool(User.objects.get(pk=self.user.pk).picture))

    def test_retrieve_me(self):
        response = self.action('me', method='get')
        self.assertStatus200(response)
        self.assertFields(response, self.user, ['id', 'email', 'phone_number', 'username', 'first_name', 'last_name'])
        gamification = self.data.get('gamification')
        self.assertEqual(gamification['points'], self.user.score.points)
        self.assertEqual(gamification['level'], self.user.score.level)
        self.assertEqual(gamification['next_level_points'], get_next_level_points(self.user.score.level))

    def test_upload_picture(self):
        self.assertFalse(bool(self.user.picture))
        response = self.action(
            'upload-picture',
            self.user,
            method='put',
            data={'file': self.get_temp_image()},
            format='multipart',
        )
        self.assertStatus200(response)
        self.assertTrue(bool(User.objects.get(pk=self.user.pk).picture))
        self.assertFields(response, self.user, ['id', 'email', 'phone_number', 'username', 'first_name', 'last_name'])
        gamification = self.data.get('gamification')
        self.assertEqual(gamification['points'], self.user.score.points)
        self.assertEqual(gamification['level'], self.user.score.level)
        self.assertEqual(gamification['next_level_points'], get_next_level_points(self.user.score.level))

    def test_upload_not_square_picture(self):
        self.assertFalse(bool(self.user.picture))
        response = self.action(
            'upload-picture',
            self.user,
            method='put',
            data={'file': self.get_temp_image(300, 400)},
            format='multipart',
        )
        self.assertStatus400(response)

    def phone_number_action(self, phone_number):
        return self.action(
            'phone-number',
            method='post',
            data={'phone_number': phone_number},
        )

    def confirm_phone_number_action(self, code):
        return self.action(
            'confirm-phone-number',
            method='post',
            data={'code': code},
        )

    @patch('twilio.rest.api.v2010.account.message.MessageList.create', side_effect=twilio_message_create)
    def test_phone_number(self, mocked_function):
        self.assertIsNone(self.user.phone_number)
        number = factories.make_phone_number()
        self.assertStatus200(
            self.phone_number_action(number)
        )
        number_object = PhoneNumberConfirmation.objects.filter(user=self.user, phone_number=number).first()
        self.assertIsNotNone(number_object)
        self.assertFalse(number_object.is_confirmed)

    @patch('twilio.rest.api.v2010.account.message.MessageList.create', side_effect=twilio_message_create)
    def test_confirm_phone_number(self, mocked_function):
        number_object = factories.PhoneNumberConfirmationFactory(user=self.user)
        self.assertStatus200(
            self.confirm_phone_number_action(number_object.code)
        )
        self.assertEqual(self.data.get('phone_number'), number_object.phone_number)
        number_object.refresh_from_db()
        self.user.refresh_from_db()
        self.assertTrue(number_object.is_confirmed)
        self.assertEqual(number_object.phone_number, self.user.phone_number)

    @patch('twilio.rest.api.v2010.account.message.MessageList.create', side_effect=twilio_message_create)
    def test_confirm_phone_number_with_wrong_code(self, mocked_function):
        number_object = factories.PhoneNumberConfirmationFactory(user=self.user)
        self.assertStatus400(
            self.confirm_phone_number_action(1000)  # is not valid code
        )
        number_object.refresh_from_db()
        old_number = self.user.phone_number
        self.user.refresh_from_db()
        self.assertFalse(number_object.is_confirmed)
        self.assertEqual(old_number, self.user.phone_number)

    @patch('twilio.rest.api.v2010.account.message.MessageList.create', side_effect=twilio_message_create)
    def test_confirm_phone_number_before_number_sent(self, mocked_function):
        self.assertStatus400(
            self.confirm_phone_number_action(1000)
        )
