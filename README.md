CREATE TABLE `profiles` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `viewed` tinyint(4) NOT NULL DEFAULT '0',
  `liked` tinyint(4) NOT NULL DEFAULT '0',
  `url` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `url_unq` (`url`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=9993 DEFAULT CHARSET=utf8;
alter table profiles add column session TEXT default null;
alter table profiles drop index url_unq;
alter table profiles add unique index(url, session);