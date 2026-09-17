# Testing principle

Test behavior at the smallest useful boundary. Unit tests cover domain logic;
API tests cover contracts; integration tests cover database and worker
boundaries using isolated local or ephemeral infrastructure. Production data is
never test data.
