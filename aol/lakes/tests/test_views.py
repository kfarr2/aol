from django.test import TestCase
from django.core.urlresolvers import reverse
from ..models import NHDLake as Lake

class LakesTest(TestCase):
    fixtures = ['lakes.json']

    def test_listing(self):
        """Make sure the listing page works"""
        response = self.client.get(reverse('lakes-listing'))
        self.assertEqual(response.status_code, 200)

        # make sure it lists with a letter
        response = self.client.get(reverse('lakes-listing', args=("m",)))
        self.assertEqual(response.status_code, 200)

    def test_detail(self):
        """Make sure the lake detail page loads"""
        response = self.client.get(reverse('lakes-detail', args=(123,)))
        self.assertEqual(response.status_code, 200)

    def test_search(self):
        '''test that a blank query returns all lakes'''
        lakes = list(Lake.objects.all())
        response = self.client.get("%s?q=%s" % (reverse('lakes-search'), "") )
        self.assertEqual(len(lakes), len(response.context['lakes']))
 
    def test_search_title(self):
        '''test lake title query returns lake page assumes unique ttile which is true of test data'''
        lakes = list(Lake.objects.all())
        # test the first couple lakes
        for lake in lakes:
            response = self.client.get("%s?q=%s" % (reverse('lakes-search'), lake.title) )
            #test that you get redirected
            self.assertEqual(response.status_code, 302)
            #check if reachcode is in redirect url
            self.assertIn(lake.reachcode,str(response))
    
    def test_search_garbage(self):
        '''test garbage query returns error/no results'''
        response = self.client.get("%s?q=fhsy78rh" % reverse('lakes-search'))
        #test context contains error
        self.assertEqual(0, len(response.context['lakes']))
        self.assertEqual(response.status_code, 200)
