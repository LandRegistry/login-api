@US053
Feature: Private Beta Log In

Scenario: Log In Pass
Given I am an initial private beta user
And I have a username
And I have a password
When I log in
Then I should access the system

@US053 @DigitalFrontEnd @GovUK
Scenario: Log In Fail Username
Given I am an initial private beta user
And I have an incorrect username
And I have a password
When I log in
Then I should not access the system

@US053 @DigitalFrontEnd @GovUK
Scenario: Log In Fail Password
Given I am an initial private beta user
And I have a username
And I use deleted password
When I log in
Then I should not access the system
