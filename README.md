CREATE TABLE `profiles` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `viewed` tinyint(4) NOT NULL DEFAULT '0',
  `url` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `url_unq` (`url`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=9993 DEFAULT CHARSET=utf8