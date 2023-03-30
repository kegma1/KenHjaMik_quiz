INSERT INTO `user` (`Username`, `Password`, `Is_admin`) VALUES
('admin1', 'pbkdf2:sha256:260000$p7BGkFkfopm6IxtN$868fc0691bd96fcbdd48f7612e0fb37406a1cd1eb4133245660a26adfb3141bd', 1),
('user1', 'pbkdf2:sha256:260000$APSdigzf27byyNaE$295eee49b7e739f91bcd8fa79149097b60ac0b28fa0bf14664d18229119104b5', 0);

admin1 = PasswordAdmin
user1 = PasswordUser