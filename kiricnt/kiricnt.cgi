#!/usr/bin/perl

#����������������������������������������������������������
#�� kiriCounter : kiricnt.cgi - 2011/07/23
#�� Copyright (c) KentWeb
#�� http://www.kent-web.com/
#����������������������������������������������������������

# ���W���[���錾
use strict;

# �ݒ�t�@�C���捞
require './init.cgi';
my %cf = &init;

# �f�[�^�擾
my $buf = $ENV{QUERY_STRING};
$buf =~ s/\D//g;

# �J�E���^�\��
if ($buf ne '') {
	&load_image($buf);

# �J�E���^�X�V
} else {
	&count_up;
}

#-----------------------------------------------------------
#  �J�E���^�X�V
#-----------------------------------------------------------
sub count_up {
	# IP�擾
	my $addr = $ENV{REMOTE_ADDR};

	# �f�[�^�ǂݍ���
	open(DAT,"+< $cf{cntfile}") or &error("open err: $cf{cntfile}");
	eval 'flock(DAT, 2);';
	my $data = <DAT>;

	# �f�[�^���� �� �J�E���g��,IP
	my ($cnt, $ip) = split(/:/, $data);

	# �J�E���g�A�b�v
	unless ($cf{ip_check} && $addr eq $ip) {
		$cnt++;
		seek(DAT, 0, 0);
		print DAT "$cnt:$addr";
		truncate(DAT, tell(DAT));
	}
	close(DAT);

	# ��������
	while ( length($cnt) < $cf{digit} ) {
		$cnt = 0 . $cnt;
	}

	# ������
	my ($cnt_msg,$flg,$newno,$rand,$kiri_flg);

	# �L���Ԕ���
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

	# �L���Ԃ̂Ƃ�
	if ($kiri_flg) {

		# ���Ԏ擾
		my $date = &get_date;

		# ����
		$rand = &get_rand;

		# �f�[�^�I�[�v��
		open(DAT,"+< $cf{logfile}") or &error("open err: $cf{logfile}");
		eval 'flock(DAT, 2);';
		my @data = <DAT>;

		# �擪�s�𕪉����ă��j�[�NNo���s
		my ($no,$date2,$rand2,$cnt2) = split(/<>/, $data[0]);

		if ($cnt == $cnt2) {
			$cnt_msg = &get_tmpl(1);
		} else {
			$cnt_msg = &get_tmpl(2);
			if ($cf{kiri_input}) { $flg = 1; }

			$newno = $no + 1;

			# �X�V
			seek(DAT, 0, 0);
			print DAT "$newno<>$date<>$rand<>$cnt<>$addr<><><><>\n";
			print DAT @data;
			truncate(DAT, tell(DAT));
		}
		close(DAT);

	# �L���ԈȊO�̂Ƃ�
	} else {
		$cnt_msg = &get_tmpl(1);
	}

	# �摜�J�E���^�̂Ƃ�
	if ($cf{cnt_type}) {
		$cnt = qq|<img src="$cf{count_cgi}?$cnt" alt="$cnt">|;
	}
	$cnt_msg =~ s/!count!/$cnt/g;

	# JavaScript�\�L�J�n
	&header;
	print "document.write('$cnt_msg');\n";

	# ���̓t�H�[���\��
	if ($flg) {
		my $form = &get_tmpl(3);
		$form =~ s/!list_cgi!/$cf{list_cgi}/g;
		$form =~ s/!no!/$newno/g;
		$form =~ s/!rand!/$rand/g;

		# JavaScript�\�L
		print "document.write('$form');\n";
	}
}

#-----------------------------------------------------------
#  �摜�\��
#-----------------------------------------------------------
sub load_image {
	my $buf = shift;

	# Image::Magick�̂Ƃ�
	if ($cf{image_pm} == 1) {
		require $cf{magick_pl};
		&magick($buf, $cf{imgdir});
	}

	# �J�E���^�摜�ǂݎ��
	my @view;
	foreach ( split(//, $buf) ) {
		push(@view,"$cf{imgdir}/$_.gif");
	}

	# �A���摜�\�L
	require $cf{gifcat_pl};
	print "Content-type: image/gif\n\n";
	binmode(STDOUT);
	print &gifcat::gifcat(@view);
	exit;
}

#-----------------------------------------------------------
#  �G���[�\��
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
#  JavaScript�w�b�_�[
#-----------------------------------------------------------
sub header {
	print "Pragma: no-cache\n";
	print "Cache-Control: no-cache\n";
	print "Expires: Tue, 01 Dec 2005 12:00:00 GMT\n";
	print "Content-type: application/x-javascript\n\n";
}

#-----------------------------------------------------------
#  �e���v���[�g
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
#  �����擾
#-----------------------------------------------------------
sub get_date {
	my ($min,$hour,$mday,$mon,$year) = (localtime(time))[1..5];
	sprintf("%04d/%02d/%02d-%02d:%02d",
				$year+1900,$mon+1,$mday,$hour,$min);
}

#-----------------------------------------------------------
#  ����
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

