#!/usr/bin/perl

#┌────────────────────────────
#│ kiriCounter : list.cgi - 2011/09/29
#│ Copyright (c) KentWeb
#│ http://www.kent-web.com/
#└────────────────────────────

# モジュール宣言
use strict;
use CGI::Carp qw(fatalsToBrowser);

# 設定ファイル認識
require "./init.cgi";
my %cf = &init;

# データ受理
my %in = &parse_form;

# 条件分岐
if ($in{mode} eq "regist") { &regist; }
if ($in{mode} eq "admin") { &admin_mode; }
&list_data;

#-----------------------------------------------------------
#  データ受付
#-----------------------------------------------------------
sub regist {
	# データ受付
	my ($flg,@data);
	open(DAT,"+< $cf{logfile}") or &error("open err: $cf{logfile}");
	eval 'flock(DAT, 2);';
	while (<DAT>) {
		my ($no,$date,$rand,$cnt,$addr,$name,$eml,$com) = split(/<>/);

		if ($in{no} == $no && $in{key} eq $rand) {
			$flg++;
			$_ = "$no<>$date<>$rand<>$cnt<>$addr<>$in{name}<>$in{email}<>$in{comment}<>\n";
		}
		push(@data,$_);
	}

	# 不整合の場合
	if (!$flg) {
		close(DAT);
		&error("投稿内容を受理できませんでした。");
	}

	# データ更新
	seek(DAT, 0, 0);
	print DAT @data;
	truncate(DAT, tell(DAT));
	close(DAT);

	# 完了メッセージ
	&message("コメントを受理しました。ありがとうございました。");
}

#-----------------------------------------------------------
#  リスト閲覧
#-----------------------------------------------------------
sub list_data {
	# ページ数定義
	my $pg = $in{pg} || 0;

	# 著作権表記（削除禁止）
	my $copy = <<EOM;
<p style="font-size:10px;font-family:Verdana,Helvetica,Arial;margin-top:5em;text-align:center;">
- <a href="http://www.kent-web.com/">KiriCounter</a> -
</p>
EOM

	# テンプレート読み込み
	open(IN,"$cf{tmpldir}/list.html") or &error("open err: list.html");
	my $tmpl = join('', <IN>);
	close(IN);

	my ($head,$loop,$foot);
	if ($tmpl =~ /(.+)<!-- loop_begin -->(.+)<!-- loop_end -->(.+)/s) {
		($head,$loop,$foot) = ($1, $2, $3);
	} else {
		&error("テンプレートが不正です");
	}

	# データ展開
	my ($i,@data);
	open(IN,"$cf{logfile}") or &error("open err: $cf{logfile}");
	while (<IN>) {
		my ($no,$date,$rand,$data,$addr,$name,$eml,$com) = split(/<>/);
		$i++;
		next if ($i < $pg + 1);
		next if ($i > $pg + $cf{pg_max});

		push(@data,$_);
	}
	close(IN);

	# 繰越ボタン作成
	my $page_btn = &make_pgbtn($i, $pg);

	# 文字置き換え
	foreach ( $head, $foot ) {
		s/!homepage!/$cf{homepage}/g;
		s/!list_cgi!/$cf{list_cgi}/g;
		s/!page_btn!/$page_btn/g;
	}

	# ヘッダ表示
	print "Content-type: text/html\n\n";
	print $head;

	# リスト展開
	foreach (@data) {
		my ($no,$date,$rand,$cnt,$ip,$name,$eml,$com) = split(/<>/);
		$name ||= '匿名';

		my $tmp = $loop;
		$tmp =~ s/!date!/$date/g;
		$tmp =~ s/!count!/$cnt/g;
		$tmp =~ s/!name!/$name/g;
		$tmp =~ s/!comment!/$com/g;
		print $tmp;
	}

	# フッタ
	if ($foot =~ /(.+)(<\/body[^>]*>.*)/si) {
		print "$1$copy$2";
	} else {
		print "$foot$copy\n";
		print "</body></html>\n";
	}
	exit;
}

#-----------------------------------------------------------
#  管理画面
#-----------------------------------------------------------
sub admin_mode {
	# 認証
	if ($in{pass} ne $cf{pass}) { &error("パスワードが違います"); }

	# 削除
	if ($in{no}) {

		# 削除情報
		my %del;
		foreach ( split(/\0/, $in{no}) ) {
			$del{$_}++;
		}

		# データ更新
		my @data;
		open(DAT,"+< $cf{logfile}") or &error("open err: $cf{logfile}");
		eval 'flock(DAT, 2);';
		while (<DAT>) {
			my ($no,$date,$rand,$data,$addr,$name,$eml,$com) = split(/<>/);
			next if (defined($del{$no}));

			push(@data,$_);
		}
		seek(DAT, 0, 0);
		print DAT @data;
		truncate(DAT, tell(DAT));
		close(DAT);
	}

	# ページ数認識
	my $page = 0;
	foreach ( keys(%in) ) {
		if (/^page(\d+)/) {
			$page = $1;
			last;
		}
	}

	&header;
	print <<EOM;
<div align="right">
<input type="button" value="リストに戻る" onclick="javascript:window.location='$cf{list_cgi}'">
</div>
<form action="$cf{list_cgi}" method="post">
<input type="hidden" name="mode" value="admin">
<input type="hidden" name="pass" value="$in{pass}">
<input type="submit" value="削除する">
<p></p>
<table border="1" cellspacing="0" class="admin">
<tr>
  <th>選択</th>
  <th>年月日</th>
  <th>カウント</th>
  <th>お名前</th>
  <th>コメント</th>
  <th>IP</th>
</tr>
EOM

	my $i = 0;
	open(IN,"$cf{logfile}") or &error("open err: $cf{logfile}");
	while (<IN>) {
		$i++;
		next if ($i < $page + 1);
		last if ($i > $page + $cf{pg_max});

		my ($no,$date,$rand,$data,$addr,$name,$eml,$com) = split(/<>/);
		$name ||= '匿名';
		$name = qq|<a href="mailto:$eml">$name</a>| if ($eml);

		print qq|<tr><td align="center"><input type="checkbox" name="no" value="$no"></td>|;
		print qq|<td nowrap>$date</td>|;
		print qq|<td align="center">$data</td>|;
		print qq|<td>$name</td>|;
		print qq|<td>$com<br></td>|;
		print qq|<td>$addr</td></tr>\n|;
	}
	close(IN);

	print "</table><br><br>\n";

	# ページ繰り越し
	my $next = $page + $cf{pg_max};
	my $back = $page - $cf{pg_max};

	if ($back >= 0) {
		print qq{<input type="submit" name="page$back" value="&lt; 前の$cf{pg_max}件">\n};
	}
	if ($next < $i) {
		print qq{<input type="submit" name="page$next" value="次の$cf{pg_max}件 &gt;">\n};
	}

	print <<EOM;
</form>
</body>
</html>
EOM
	exit;
}

#-----------------------------------------------------------
#  フォームデコード
#-----------------------------------------------------------
sub parse_form {
	my ($buf,%in);
	if ($ENV{REQUEST_METHOD} eq "POST") {
		&error('受理できません') if ($ENV{CONTENT_LENGTH} > $cf{maxdata});
		read(STDIN, $buf, $ENV{CONTENT_LENGTH});
	} else {
		$buf = $ENV{QUERY_STRING};
	}
	foreach ( split(/&/, $buf) ) {
		my ($key,$val) = split(/=/);
		$key =~ tr/+/ /;
		$key =~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("H2", $1)/eg;
		$val =~ tr/+/ /;
		$val =~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("H2", $1)/eg;

		# 無効化
		$key =~ s/[<>"'&\r\n]//g;
		$val =~ s/&/&amp;/g;
		$val =~ s/</&lt;/g;
		$val =~ s/>/&gt;/g;
		$val =~ s/"/&quot;/g;
		$val =~ s/'/&#39;/g;
		$val =~ s/[\r\n]//g;

		$in{$key} .= "\0" if (defined($in{$key}));
		$in{$key} .= $val;
	}
	return %in;
}

#-----------------------------------------------------------
#  HTMLヘッダ
#-----------------------------------------------------------
sub header {
	print "Content-type: text/html\n\n";
	print <<EOM;
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
<head>
<meta http-equiv="content-type" content="text/html; charset=shift_jis">
<meta http-equiv="content-style-type" content="text/css">
<style type="text/css">
<!--
body,td,th { font-size:80%; }
table.admin th { background:#ccc; padding:3px; }
-->
</style>
<title>管理画面</title>
</head>
<body>
EOM
}

#-----------------------------------------------------------
#  繰越ボタン作成
#-----------------------------------------------------------
sub make_pgbtn {
	my ($i, $pg) = @_;

	# ページ繰越定義
	my $next = $pg + $cf{pg_max};
	my $back = $pg - $cf{pg_max};

	# ページ繰越ボタン作成
	my $pg_btn;
	if ($back >= 0 || $next < $i) {
		$pg_btn .= "Page: ";

		my ($x, $y) = (1, 0);
		while ($i > 0) {
			if ($pg == $y) {
				$pg_btn .= qq(| <b>$x</b> );
			} else {
				$pg_btn .= qq(| <a href="$cf{list_cgi}?pg=$y">$x</a> );
			}
			$x++;
			$y += $cf{pg_max};
			$i -= $cf{pg_max};
		}
		$pg_btn .= "|";
	}
	return $pg_btn;
}

#-----------------------------------------------------------
#  完了メッセージ
#-----------------------------------------------------------
sub message {
	my $msg = shift;

	open(IN,"$cf{tmpldir}/message.html") or &error("open err: message.html");
	print "Content-type: text/html\n\n";
	while(<IN>) {
		s/!list_cgi!/$cf{list_cgi}/g;
		s/!message!/$msg/g;

		print;
	}
	close(IN);

	exit;
}

#-----------------------------------------------------------
#  エラー画面
#-----------------------------------------------------------
sub error {
	my $err = shift;

	open(IN,"$cf{tmpldir}/error.html") or die;
	print "Content-type: text/html\n\n";
	while(<IN>) {
		s/!error!/$err/g;

		print;
	}
	close(IN);

	exit;
}

