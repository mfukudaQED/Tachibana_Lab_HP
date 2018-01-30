#!/usr/bin/perl

########################################################################################
#
# ■アクセスカウンター・プログラム
#
# ■作成者: 情報環境部 情報基盤課 学術情報基盤グループ
# ■作成日: 2004.05.07
# ■最終更新日: 2009.08.24
# ■機能
# 集計したアクセス数から、GIFの画像を連結しアクセスカウンターを表示する。
#
########################################################################################
#
# 基本マニュアル（基本的な使い方）
#
########################################################################################
#
# ■設置手順
#
# (1) プログラムファイルを解凍すると，counter フォルダが作成される．
# (2) public_html 以下の任意の場所にcounter フォルダと，その配下のファイルを全てアップロードする．
#     ※ただし，サーバ上にすでにcounter フォルダがある場合は名前を適宜変更する事．
#
#     counerフォルダの内容は以下のとおり
#       count.cgi (本体)
#       gifcat.pl (画像結合用スクリプト)
#       data/  (カウントデータフォルダ）
#       images/ (画像フォルダ)
# 
# (2) 下記ファイルのパーミッションの設定をする．※（）内の数字がパーミッション
#     count.cgi (755) 
#
#     通常は設定の必要はないが，動作しない場合は下記パーミッションも確認すること．
#     全てのディレクトリ (755)
#     data/配下の全てのデータファイル (644）
#     gifcat.pl (644)
#     images/配下の全ての画像ファイル (644)
#   
# ※Filezilla の場合，ファイルを選択して右クリックをし「ファイルの属性」でパーミッションを変更する．
# 
# ■利用方法
# カウンタを表示させるには、
#     <img src="[設置場所]/count.cgi?[画像の種類]" />
# というフォーマットのHTMLタグを，カウントしたいページのHTMLソースに記述する。
#
# [設置場所] には、count.cgiを設置したパスを指定する．
# [画像の種類] の部分には下記のいずれかを設定する．
#
#  blue  green  red  white  black  yellow 
#
# ※この値は省略できないので必ず指定する事．
#
#   [コード例 (画像の種類に whiteを指定)] 
#   <img src="/counter/count.cgi?white" />
#
# ■カウンター数値の変更
# data フォルダ配下の default というファイルに半角数字で入力する．
#
########################################################################################
#
# 応用マニュアル（さらに便利な使い方）
#
########################################################################################
#
# ■新しいカウンター画像の追加
# １．数字の画像ファイル（GIF形式に限る）を10個(0.gif-9.gif)用意する．
# ２．images ディレクトリ配下に新しいフォルダを作成し，その下にGIFファイルをアップロードする．
# ３．[画像の種類]に２で作成したフォルダの名前を指定してアクセスする．
#
#   [コード例 (追加した画像フォルダの名前が"newcolor"の場合)]
#   <img src="/counter/count.cgi?newcolor" />
# 
# ■新しいカウンターの登録
#   複数のカウンターを設置したい場合は，下記手順を行う．
#
#   1. data フォルダ以下に、カウンターファイルを作成する。
#   2. カウンターファイルに，カウンターの数値（半角）を記述する． 
#   3. 
#   <img src="[設置場所]/count.cgi?[画像の種類]&[カウンターファイル名]" />
# というフォーマットのHTMLタグをカウントしたいページのHTMLソースに記述する。
#
#   [コード例 (新しいカウンターファイルの名前が"newcounter"の場合)]
#   <img src="/counter/count.cgi?white&newcounter" />
#
########################################################################################
use Fcntl;
my ($locked) = pack("ssL", Fcntl::F_WRLCK, 'SEEK_SET', 0);
my ($unlocked) = pack("ssL", Fcntl::F_UNLCK, 'SEEK_SET', 0);

$ENV{'SCRIPT_FILENAME'} =~ m|[^/]+$|; # $` にカレントディレクトリが入る
my $cgipos = $`; #CGIスクリプトの置き場所
my $datapos = 'data'; #カウンタファイルディレクトリ
my $imagepos = 'images'; #カウンタファイルディレクトリ
my $defaultname = "default"; #デフォルトのカウンターファイル
my $lockfile = "$cgipos$datapos/lock"; #ロック用ファイル

require $cgipos . "gifcat.pl";   #画像結合用スクリプト

my $mode;
my $input = $ARGV[0];

#CGIへの入力からモードを解析

if (length($input) <= 0) {
    &disp_error("Error: No Parameters\n");
} elsif ($input =~ /^[^&]+&[^&]+$/) { #入力の要素が２つのとき
    ($gifopt, $name) = split(/&/, $input);
    chop $gifopt;
} else{
    $gifopt = $input;
    $name = $defaultname;
}

my $countfile = "$cgipos$datapos/$name";

#画像フォルダが存在していなかったらエラー
if (! -d "$cgipos$imagepos/$gifopt") {
    &disp_error("Error: Not Found image files\n");
}

#データファイルの存在をチェック
if (&sub_id_tbl_chk) {
    &disp_error("Error: Not Found data file\n");
}

my $lockstart = 1;
&sub_counts;
&do_main;

exit(0);

#画像を結合して出力
sub do_main {
    
    print "Content-type: image/gif\n\n";

    open(OUT, "+> /tmp/out.gif$$");
    $count_m = $count;
    $len=length($count_m);
    $len_kp = length($count_m);

    while($len) {
        $moji1 = substr($count_m, $loc, 1);
        $moji_join[$loc] = qq{$imagepos/$gifopt/$moji1.gif};
        $len--;
        $loc++;
    }

    print &gifcat'gifcat(@moji_join);

    close (OUT);

    system("/bin/rm -f /tmp/out.gif$$"); #作成した一時画像を消去

}

#排他制御付カウントアップ
sub sub_counts {

    # ロック
    open(LOCK, ">$lockfile");
    fcntl(LOCK, F_SETLK, $locked) or &disp_error('Error:Can Not Lock'." $$ @_: $!");

    open(IN, "$countfile") or &disp_error('Error:Not Found Counter File');

    $count = <IN>;
    close(IN);
    
    $count++;
       
    $countfile_tmp = $countfile . "tmp";
    open(CTEMP, "> $countfile_tmp");
    print CTEMP $count;
    close(CTEMP);

    rename("$countfile_tmp", "$countfile");

    unlink("$lockfile");
    # 解除
    fcntl(LOCK, F_SETLK, $unlocked) or &disp_error('Error:Can Not Unlock');
    
}

#カウンターデータがあるかチェック
sub sub_id_tbl_chk {    
    if (! -e "$countfile") {
	    return -1; 
	}
}

# エラーメッセージを出力
sub disp_error {
    print "Content-type: text/html; charset=euc-jp\n\n";
    print $_[0];
    if ($lockstart) {
        unlink("$lockfile");
    }
    exit 1;
}

