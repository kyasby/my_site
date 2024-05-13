#!/usr/bin/perl

#┌────────────────────────────
#│ kiriCounter : kiricnt.cgi - 2011/07/23
#│ Copyright (c) KentWeb
#│ http://www.kent-web.com/
#└────────────────────────────

# モジュール宣言
use strict;

# 設定ファイル取込
require './init.cgi';
my %cf = &init;

# データ取得
my $buf = $ENV{QUERY_STRING};
$buf =~ s/\D//g;

# カウンタ表示
if ($buf ne '') {
	&load_image($buf);

# カウンタ更新
} else {
	&count_up;
}

#-----------------------------------------------------------
#  カウンタ更新
#-----------------------------------------------------------
sub count_up {
	# IP取得
	my $addr = $ENV{REMOTE_ADDR};

	# データ読み込み
	open(DAT,"+< $cf{cntfile}") or &error("open err: $cf{cntfile}");
	eval 'flock(DAT, 2);';
	my $data = <DAT>;

	# データ分解 → カウント数,IP
	my ($cnt, $ip) = split(/:/, $data);

	# カウントアップ
	unless ($cf{ip_check} && $addr eq $ip) {
		$cnt++;
		seek(DAT, 0, 0);
		print DAT "$cnt:$addr";
		truncate(DAT, tell(DAT));
	}
	close(DAT);

	# 桁数調整
	while ( length($cnt) < $cf{digit} ) {
		$cnt = 0 . $cnt;
	}

	# 初期化
	my ($cnt_msg,$flg,$newno,$rand,$kiri_flg);

	# キリ番判別
	if ($cnt % $cf{kiriban} == 0) {
		$kiri_flg = 1;
	} else {
		foreach ( split(/,/, $cf{kiri_op}) ) {
			if ($cnt == $_) {
				$kiri_flg = 1;
				last;
			}
		}
	}

	# キリ番のとき
	if ($kiri_flg) {

		# 時間取得
		my $date = &get_date;

		# 乱数
		$rand = &get_rand;

		# データオープン
		open(DAT,"+< $cf{logfile}") or &error("open err: $cf{logfile}");
		eval 'flock(DAT, 2);';
		my @data = <DAT>;

		# 先頭行を分解してユニークNo発行
		my ($no,$date2,$rand2,$cnt2) = split(/<>/, $data[0]);

		if ($cnt == $cnt2) {
			$cnt_msg = &get_tmpl(1);
		} else {
			$cnt_msg = &get_tmpl(2);
			if ($cf{kiri_input}) { $flg = 1; }

			$newno = $no + 1;

			# 更新
			seek(DAT, 0, 0);
			print DAT "$newno<>$date<>$rand<>$cnt<>$addr<><><><>\n";
			print DAT @data;
			truncate(DAT, tell(DAT));
		}
		close(DAT);

	# キリ番以外のとき
	} else {
		$cnt_msg = &get_tmpl(1);
	}

	# 画像カウンタのとき
	if ($cf{cnt_type}) {
		$cnt = qq|<img src="$cf{count_cgi}?$cnt" alt="$cnt">|;
	}
	$cnt_msg =~ s/!count!/$cnt/g;

	# JavaScript表記開始
	&header;
	print "document.write('$cnt_msg');\n";

	# 入力フォーム表示
	if ($flg) {
		my $form = &get_tmpl(3);
		$form =~ s/!list_cgi!/$cf{list_cgi}/g;
		$form =~ s/!no!/$newno/g;
		$form =~ s/!rand!/$rand/g;

		# JavaScript表記
		print "document.write('$form');\n";
	}
}

#-----------------------------------------------------------
#  画像表示
#-----------------------------------------------------------
sub load_image {
	my $buf = shift;

	# Image::Magickのとき
	if ($cf{image_pm} == 1) {
		require $cf{magick_pl};
		&magick($buf, $cf{imgdir});
	}

	# カウンタ画像読み取り
	my @view;
	foreach ( split(//, $buf) ) {
		push(@view,"$cf{imgdir}/$_.gif");
	}

	# 連結画像表記
	require $cf{gifcat_pl};
	print "Content-type: image/gif\n\n";
	binmode(STDOUT);
	print &gifcat::gifcat(@view);
	exit;
}

#-----------------------------------------------------------
#  エラー表示
#-----------------------------------------------------------
sub error {
	my $err = shift;

	&header;
	print "document.write('<h4>ERROR</h4>');\n";
	print "document.write('$err');\n";
	print "document.write('</body></html>');\n";
	exit;
}

#-----------------------------------------------------------
#  JavaScriptヘッダー
#-----------------------------------------------------------
sub header {
	print "Pragma: no-cache\n";
	print "Cache-Control: no-cache\n";
	print "Expires: Tue, 01 Dec 2005 12:00:00 GMT\n";
	print "Content-type: application/x-javascript\n\n";
}

#-----------------------------------------------------------
#  テンプレート
#-----------------------------------------------------------
sub get_tmpl {
	my $key = shift;

	my %tmpl = (
		1 => 'count.txt',
		2 => 'count-kiri.txt',
		3 => 'form.txt',
	);

	open(IN,"$cf{tmpldir}/$tmpl{$key}") or &error("open err: $tmpl{$key}");
	my $tmpl = join('', <IN>);
	close(IN);

	$tmpl =~ s/[\r\n]//g;
	$tmpl =~ s/'/&#39;/g;
	return $tmpl;
}

#-----------------------------------------------------------
#  日時取得
#-----------------------------------------------------------
sub get_date {
	my ($min,$hour,$mday,$mon,$year) = (localtime(time))[1..5];
	sprintf("%04d/%02d/%02d-%02d:%02d",
				$year+1900,$mon+1,$mday,$hour,$min);
}

#-----------------------------------------------------------
#  乱数
#-----------------------------------------------------------
sub get_rand {
	my $rand;
	my @char = (0..9, 'a'..'z', 'A'..'Z');
	srand;
	foreach (1 .. 10) {
		$rand .= $char[int(rand(@char))];
	}
	return $rand;
}

