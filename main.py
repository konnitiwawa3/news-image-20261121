"""Render the 20 November 2026 front page as a deterministic PNG."""

import base64
import functools
import json
import math
import os
from pathlib import Path
from random import Random
import struct
import zlib


SIZE = 1024
SCALE = 3
# Astryx Stone Light: Yellow 90 on the paper side of the mix,
# Neutral 15 and Orange 30 for the warm tone of the printing ink.
STONE_YELLOW = (244, 225, 183)
STONE_WHITE = (255, 255, 255)
STONE_NEUTRAL = (37, 37, 42)
STONE_ORANGE = (94, 63, 39)


def mix_color(first, second, strength):
    return bytes((a * (100 - strength) + b * strength + 50) // 100
                 for a, b in zip(first, second))


PAPER, INK, HALF_INK, FAINT_INK, RULE = range(5)
PAPER_RGB = mix_color(STONE_YELLOW, STONE_WHITE, 13)
INK_RGB = mix_color(STONE_NEUTRAL, STONE_ORANGE, 20)
PALETTE = (PAPER_RGB, INK_RGB, mix_color(PAPER_RGB, INK_RGB, 70),
           mix_color(PAPER_RGB, INK_RGB, 45), mix_color(PAPER_RGB, INK_RGB, 57))
BODY_INK = len(PALETTE)
DISPLAY_INK = BODY_INK + 3
BLEED_INK = DISPLAY_INK + 5
PALETTE += tuple(bytes(channel + delta for channel in INK_RGB)
                 for delta in (-2, 0, 3, -4, 0, 4, 8, 13))
PALETTE += (mix_color(PAPER_RGB, INK_RGB, 32),)


# Monochrome glyph masks measured at 3×, compressed with their metrics. The
# Source Sans 3 and Newsreader license notices are in fonts/.
FONT_DATA = (
    'c-ri}+p=uERUiH;u**OwwqvQ)tEILpMR73Z7%=$n0RPGbOG^p_6B`U9hDuc`Z;|WV=05j43Qv-jG|tlOp1n?cZ~Obc-8#(GJ*TD)Lqp^68~^;_@rO@8@rMuJ{O1pU@!^~QzdwI;AHVL?$4lXoesG~C=X|aCk``Z_bIG;TxhT@=`j=Y0rM{-vzTf^Da!->=+jny4-yFZnm+K$?<Hrw=mo^++Ys2B;<E3y(Klt1pu`liIthI<XTpoA%>qz(ilfP>BsjkwUbL*4V+T409Vvn6hk6j*o>4kFnesN{AtbH!GT7Tg0y>HuZ+HWuSX!n0w^oAQh+mrg*(#wdXcIQhfdn1f=_do6pyc^s(w5PPz7Bzno_lE25)PHqJ`>cSw$w$<7H%RB#5u*(AulBju=iB8ed5lPHZScLvF2iy7cu6mF`0|6+05KZ!(<XQOtp0Y-r#=5anKjf$Y%HJH)7r+_m$3q%Cphib$9FE@Z*SXQ&uz_j=!yQN-gB*A_2h-#Ep6P!{Jq>6=I>v=aJ9wu=1+RXC%bxHC2g(!t4nJWG&YU4rjSGSeTKC5-2T7a=Rf!ReEraG<lV<`xQx*Ws95`)oc=Gq(Fdj_j>ccNxq~n0)7_&1ecxwRpJjQ_mQD&9fo+tlrB9`&Otc4~@Fff?pZN~3W}>)1jK&XIYjN(Jsj+YNfx&5y{+r9AgM&pDd?z%0GPVV9nU0|?=9+3-M{P>BJ{b*<@0PcA{uf$aZ8ROX^Bot>4;O8iiLw_&nKp*okC4@Z8w1_h<HY`vX~UQ+Z?jdW#a6w45w+I-?V`2sxs~qU;9G0|t}VlW8%}^ZR#RKvezep1^85|$$L;<Pc>jkne`2FrmuFl^uVQ5i40`MOzR9#PCI%-T8X3C$BDBeW`A)n4-&6Y!$JYK!`k`;|i%;9@`+mRi_p6`5EObKBp8F5WwfXvM5Y|N*{Zb!$H^JEbqhcRpZ$s=Yg@4E{7fOL31Bs^8l|CtC8bjZ@BB!Bn+Bt{ThX307;e`Egf;NoV9n;7|x^!C4Lme%GJdgac#e{@;Z(kgF8M!Ob=boSZQ*Uk2`DH$hypwRwL#EB~zqP(PX;%BvKbLoH+g97ILa(_R$NR?7UHyGqxwLr``*zqi#+J7CyL_{@`~Sp@MO*dP$HGrz;R>X!?I#!o9*ZzWp_);^R1zbx&c)D0qEY{}Se2Jml|$z-JE=+zxNTbgtvA}`=+vJA{^Ii6_G$P3wZX=I-S=gA@MBr_Jy@mTF_|>>H<0PzW{abA=6((D-=`iN9O-M7eu%ef4gK{teLav5XeXRjJ69~ZmYo|(O|&gBN8R3}^fYdymA})zKYrWq)7tqPs-151XQxMSItY2(%4Im;%$w6)d&BY$?aoJhN*F9&e|m38Yv*sab{?>u2kg(p8>*9i;$_d29lf-bPIpiv!i)lvgKyJ0t8E)+Z0G3n(L(3$Pw^?mJ^v2WhStvCVxIokdHT<#ordZ8P8;{2#~t?Y@t84NVm};hP^~Mou~tqmHyNp#1LNjJP~6KCY2bTHT04KcweyJW9PGk#=9@`tBNmXp_-?J8zr&}a<Hs{K^DRH^vA;{ZSetGUhVkW7<T+`8eJFOuwr>}m)U<Z~-imDJHVcTfu;^{qkrrlZPaiw^KlgMcZqY{=-T{gr<bzB6{Y8I%n%=xlX8wS<xYnPi(N5g@D{|({p<^Cpeqq5*kQbR>SU1Q!7sq+@irb?+JUX3M;FOBaNkEEX1}F3OUjJT^r9kh61f#tZr~Uk0+c3Ab$1doIz5TJzli24>PgCavGpD}uhJ!<FJY<_EBOS5>k@`B#lRs2s>4@ZWoPzuLE_ESff3bq3qVb@djyb(Qo$tWpvlVin9kaKjweyd5uuIoBcDY51jd}<dE2#=zxE+1h_UHL?=+CVB(+Xh+x86zI<#5~H;*YQPc6!C$UWn`@#oMHHgNgnV76TJAHAL!-aQA~mKf^k|ErcHDfqwGuvVs2FLK4QoO27`Fr1_MNn|l&h_xqH7A7J{vw_y4%CziJ2>tJJx&<}i?w6*j9TT!i-Gby`MI75toz|o|B%o_uPhm!B>Q{Fh0)a3!K&p9c>nh$7^CZ9O#!I8L5r^0bCR_Dj*bV)*r|Ij)Vx#+{-qQ}DQGqaO{mM4)nesjn#JmycSuY$|wF!FQmiy?5{m&j!o>w+81<B+I`JVwmBP-EnmUhVmXHU!LvZgU*pP2S$?PgfIK$`iG2X!K{{K0Ig9d&%}*72<|RA&dYa1)s+|v0y!Ig0UXs-rD(RgAIa-0u8Mw6xooD2pLsZENJP}mR#!j8%JyCpG!&x6WVv$;DJJ*R3&NUwK~p(>5KKgFHQ%f(4Rii)=sxL7Q%pm+D{D+PlC(9xch|7v+UU{T3D!3>DXJ++UdESU9@~jKfvpaEwGC8UFa+Admyklta?%~3ZZY?gEAg&JYdJrN{QY0%JfIL+*=r_oncoygH~~0ZDC9xx1r57X!W=?(ulnWn4w8s`d3-a+}e3ujySxNNXI<sQrj@nvlRJ}G!*zM!Cis4taCsk-M`3N3m+COyjvhrS@Py{D7X5}^dSo??6%rlcv_9MLw>3c-B@=Aw-WX(1SoxmJa#!uRm6Hrvqb4Ix43);CzYjME-rdfiefc|bXNsFvXf3%r|>=WJgs^%FpoKQ7Mxu|Pcmyu#+(H9z49HpJ~ku}KvgO7*Z=UIMrzvIdEQ*zV`Ysq2F(BDq_C@OJgb6!r9CU6iInN+W#@X3=&$51KX++o6KA-OE&b3g{oBi>&Vn>8J}B{9590@y-ADZ1vDr*`4+4hDA8FS>iUlyCXm|J}yu)shm`m<O|Fx(7>;L#)^ju}AQ25hl>}lB9pskj7FMsye$r@>N*(LoDIwO#G{r;QS^2?Muql$7Gom>BHjp(=3-474XySsgY7fM$g$37Lsd;LOV({L&T(1x_tn1?Bs?~A2S9{R+Jl%GtVNA59Coq;XE*V6Nln{+pyx|Xu0(~v;Btn<syVB|+0AU{BUa{c$NogHe=ecx|}p1Zx**O;I0=5O7yXp;~sBaG2w$J+<&%*+?^{Nj?Yw>B}qLB_5fX#e$p{-5QRrumm4)L#)N`8JX<GS|sS&d=6<+UC^L6H&YXC#rw>--{!a-FvB_dzenqeV|<(opxRKHtm~oUu_Nj2HQP6G`oi}RRa7J=}`gOKctC?KLOU1{mGS|$)BvA)Y|oL*nl!Nk`?;NB<mYQ@#DpE-}_Pa87FaHG$^4jGU@o`*1iL_@6g*feSLM$2rP5h`!T;g&F_g{mF@d^?!SlDf8BcMIrb{{Bmc7-FHHVlB^!zM?9+I5EPahMe!vS`95x9M)&kN}K=y_FuYW!B2W(k>aUt^}5d@zMlxRo@G=_wr$}<g`JY4v<wq>T!iFqTv?OhrReId(3wqH7v+a>>9ywVJ?yZ*5DPwY~B*G;N_g$Y?V`njYZ_Vc8%uiug0A)mOi#sACyrCqpjMgI8wUAW!u-_h$0d!kGFK{a~EfA@YLpZ?!J4rhWRIun5G`_N_I{Tw-F(Ae_u9N)M7Ht-3Kmcgcx$!=}Rz01xSx(GYu^}iuvBdO0NJ@?-Z_SgwmgFa&$2NIeg=?6cX<?KpBx3oh!Q@7u5TB6#;uLaX_;@+Q%-;TS5!f({|2e5NXcZ4(adE5KA&&M$&NJI4Gla#Y6>BX+J%*;u03GW|J(Sc`La%eDpZscn_(!;O_$yIX`Q=bnNQOLW~WuMm}tmv#-?bIyxHaK#6;CX(4KKH866Zd%-w=Mk7wxK^urBY?G?DM1O^FoJQoE4QgjZ2^V&TkJ3;LuljB2zK*L2Juyak=>Wb3W)I0VYPh#|G!)Sgjp}XsCkoO-!)fx6<~_-owz_%vwjQ7^>(rk!j|j;YVK-O{!zkI&8XNb@OkXm<fMr=eBzmJvnaC6P%ESGQ4_<t`>uf3H{*O=gflZm=1#F^*`vc;eGenXblP<kF7xqR%G7H(z|_P9lT37rf}@jalno|_~%ZFk&b_%@Wda>qM~o!W#Sa}<A_~ACj9s6Q{gmKv9RXlMZ}3G#SiSH@WROCJwDy!B@I=(7p@>jASR)ku6<y+QQshkk>zDECA4F#PtYG1o-z%sek1cBy?{6WJWJ$O5|DrfeCOjZwfVG!<A=6wydC=O?NHw*kiPn6D%${if4@lEAxj8wMgGXN5Lu8hTi&0IYpX4evsb#GDv-m<^hSr#=NZha-<?S!M(s}aj+|N^kdb|$Rec$u(j14z!7lT5^uq1s$86?z=w^P*I1kmDP%nkPMQ^ghVCEv!a=uFawt3}4Ps1=_8}~<r9P)7NCUZowM>m4_u*GCGUn2ZGpIJ+z{joEOxsexgn;CP>Bkg%>x<V6H&9XkPyFB&?ee{p4{P$h?@4J<VD|(Y7*R_=c+i-*fr5QN0f%{NT&xKT-kUo)0O{K012b+Mc3eYMrv55W1+gZ$!=Pty+yeqKEu;3Yax4gu>bQNobJoe5CxyxDV<=$QJe#y@x56vnzKBjI8(!?X(6{!v(av08HBL`-q3dfr>w7(rHJ=v&a)v=Z2*kDQk)+u>uodR|#Lk9jhEP}}Jfeer;njT?Kp+(A1%vd+RYS^e*h6V>34B(1%%7RfIB0e$J-DzpKE~!x#W9?Mx*1A%At`3zAonleWJPCU^^&TE1Tc)c6`i61J{FT|z#h5B2m7)s}tn@DK?-WOw0E{;%GOcWp4c6IR<T_ID6%-q|F#aEl9Zc4QH9p(q>z$u(i|OF<dP<%_Cv5)-C}u_ajE0J!Acaw_@NO0QW=9?q{NCJ`?r-i3I1l8|eCvbX3-CJ>p203r@wvED{05uOcI`($y3uA<@XNy%DT1G0<BsaJIdXSew!{^5DjQEnt0<5Jjuy6Uk-U-SF)ZQ$FZvpmSA|t6$Fi8dzjF-sj*-1TJ{Q{o?Fx3Tz<Ury__kVmf#xple~`NSWoP(2l|Ju2j%T<?(d!9>Vx645Zu{TjEjT4_s1vTC6Rx3ylwZ@L3owvlHut&h6Wx<?FcYU7jJ5XUVK`t-`LMFsJT05~IJU&m&LY}P6A<KCpsFWttAyj2u5z8P_o;+uqVxCpkoVRB_4tQ(dhfX%zsp?CSV!Fr0{8S!oq8}*aup@d5?_Y-^6u>QfN$|Yy-8G3@1#V%ac4&Ao&og-m>y)kVC|wC1{m|zSmh$U<nX%!_sNhaxIgCfT;4@CI0H-V<=F|H$7U+{I#lYlQ%jrCsVv|s2)GK813AlJWGT;_H?!^m0WlcE3VC<Iuk4CXF8MuABOfZ>o~NGYkvCQn@^0|o?DD(ee?J+Cyh7e#Uql`-2ZsUY7CAYcO;it+B-!M}<ftr(n8O)7V4ig@FrO;S=L)A1$kWIJ=6U2E^8)h@^Gb36od=V9k&_c!!d)*Z&XG7XFLu2wyc%j!+?0oPpm&}GJ7k9A&<k?#q_FqL=h9lFzh&O_vUm@CFWBA5Np7N7d~&FUv#<7Ku*Gd|<V61zm&ng4ijHZn;<a*ex|8F7dZY0VpXK;hp)uk^E*{s(SdM)By5SwU`MqGi?4BoPzR(FUE$0dDlelkUj{BUi&)x5UUi=9wa?hynWJPX5rU2#6Zpf5QD_M4xveWE@p*C9>l5ff|3{pSYWKw(rnYC5k2CWtN9=}WKYWy_pX1WxW($9wVQYpC{%027+{v7MGKhe?&T&rcw!5|isQ)~8wwCnq0{JMu49htknsqd1*8a~Q&Qf-izt@)RMdEhVipQ{@VCk;+J+R?x~0<=AtyIIU|n!4!X81Tp+M*E>Z#*z%S1XK`86;1AA+$=S*=TJ#CW+NsrgD*oSw<<L@YuMQ~2E}7354oNxm0`UXx-UJr8$#)EU8*DsMuX;CrGR#-f4W+*VvsgXY~&<>$uR_$wb&7gk{)Fm%P`VBrY_qQi>J`kVdE5XqmBt(Di4k(?13gMv42{QP5-<Qaf9qy=_#a!qUM!W;^is1S{fNum)0hkvPg0Ekh@QWU2i+#ZTac-mdF%cFxBboYz@VS>pKtaOdG;X8=jTUcg8=Zm>C?f3T>ir&^(~Ic6*E1rSv@FbxPlTe^R<`a)CXpPRGh8qK@@m6Ka|^4MbNOkM*RHKx$i_oBT_jKSibJ&^gVYptQx*evdNtJuPP)QK(XBBpIH#C1l4mIDq_(8FV^`v_0m}Nw|B?^T$o<Oi<K~w6_z?i(=AR9^74{fQ^U<c1bV-acG*VO7~AGbOTi_2d>*lh41h#Mt+*O=x##nj@v4YS<5$io{W%n&u3{acv{k*AQ0gO_dIa7lFJK1x^P(T&a9WcsjZr);dI_CVg`RO_~0e|F)0>qS<}SD{F&E_@fejl$*Ydn^Vj3Xu5_Q-47!%?qW@s|SwKO#NQd~S4)4z4$6eVs3GU_rNF~ESjN4wZvLRa`HaBID&LA95r?>C|ex<@&RB7Qi+t6NVLjkLR*hNdF3zTw2Nc`1?Yj=6XRFrUTSxSh14v@Xw$0XfShp}OIqXAKbv_I_&;mFRZ;@duegt;24L3C&VrylfDMFes5QU&C;b92~iJ$lQA2%W9mPEU>dd{^1#(vcyqIzL%|t~-22p5@Wnwafm{?2s;LTkj4(d++m2c9ZhmP3o}E!1$&o>c#~5mVMs&6`uFZ8TJcovwChet0Xt^8NoDsLW9YW&}edC$fg0z0;LnULuSC_7+`8p@?1(-3S2^0%6xKwsFhDcvv|341|4HO53&2DExvnPbqz`?V0#^gJRMFSqjaKDp;E?@=MotALsXCmR1K7nk<_dwI+PW$dwz}Ws=Iqp7<}*A?bWZj`bPAwY!p?%dZB`p-Pzo>7;2lx8yqZfK?2AG>ERXB3E_vk!8N$bi0Yw$0PnOoVa)`4n3KrV{#B=b-hhcWI}kbrvcXxY1j$QxV*Zso@!0Z^`8jG!tF2V9i3<a&JB|&ao0iP~H^@M>k>v-NeqQ+7?r<Y@dE+Nnylkx(?Tw$1M{k#uv``6$kD*VQBwSf%vV|}XFY)g6n<(sCUcPzZ<;!jMTR+>nzx?vv&qkOI+xPP8%JUZmA`QvD_48|n3t4VKNq-K)6Bt!F9#nZVl^76_$zNSneuwel7LNICA6SL{B~vne{>8O14t79s>|8+XF&sk?Yj~C8-+{uWai3wXisxOTbOS{mBOAcu8jULvky<ihDuLmD1>lR0MjMAA^`QHpxvC>#LO@}`*qAEDgMe-FMDy!c*cc>q^X716%iBm}r(iO@_YOCGnE~(Q)cNq!%egG{YKB*LAIHBBt5@0Q+kF487Jkk@c=C>drj57+-RIsnpZl>_bhgc>v5|Eq1Q7aTjhX)+sQaP2G=z+v$>5IQyE{TN2rkza3#Pnv25=@APUHjocSkzDFB}nun47$dkNBp?@utHhzX^L&sD3Pyy!iC{`LVeVsRa20+c&-amR)<m4jI7lL;}6tlaB8zv!!}2?9&U;6&^m0e;D(mzd@69wH4n|jGE9t;E#CeOMKG~t!x65^&PFhDF!C1MJ<uo5lzR(9%ycTC<qzN$v7|$BD0$)n(S>I@`{o6D~O_9*6=1(#_j23u<su+h1rEgc*gQ5r#t3z6f+s-bG>UmZ=~qsiq7)qaR5yWx?rKFBp}1RAM{{7kDz0RegJJ8<53?}uN`Ec^Qo%<W6z>1qvyu^!0O3@-nc1EoQ`h-9TL<C&E$SS<KRD@sZB5b)Uk=<!5p1M54bLxAJt`DUsmv-2T!%&Sz+X%o;y;y?>q8q=jg}@F=u)R7i`aH&0Ea*AF3xtpy2{fZ_xZPT0kxP>fT5PjMVtPmyT<sr~Q$6VxvVNzrjA$t>3QCV|13Z?HNkb*WOJYZ>}tIbv$5u0?vVSnE}8<BvO3ur8Ph1m|%2IH}GdWyBX7IXrhaQ`-73DXUoG_DH16=AdYsP+y3Q^fyvmnium0v`jnVJg+k7S0A9oE;l=ZQtRLL@hLL2d>@sM%w;mO$eJ&&0_C@?3uJ%v2VW?nh84G<Vq89f4A;3M`YHHkG$RoYvh0{}M&djCXy;PBQ%Z<_vYCG5qrKOuN7aJRk-vV2Yt+uU&F>ltRjgAN8M=$N5cv#||o#p19S@%kXUWwv40g)gx9DiUwXW{&2xXLgT_5Cx#R=@)21|FG=4KbpHba<ucRRgZNP1f_6tU(CuAO#TWM9@<eRGXPm6gbt4NM+)f9Hlk!KlDO_Dcuj^ttCMi$051dBJrVU*f|hr6$s)nrM@N>dKKJ+(Ju@L-?@|iGlBd^)Oq%0dD1b;V&0nuw9+|XNJm#WCN#(B{Y{RMOQRD6J`uiSVEsR)!!m47Dt;BJ*(!)J{WeeXb6+^4C51jq#)2p3#^34p6anh~XJq>9Ao$-|^yuc;maVbvct9!@ZnuR~4>mEC16R`6{x*kIJom7Q=g!XUAGeqlSURM4-T{4huuIO^4)<Cg3btfMcH'
    '{Va^W$5er$NF-c+5<`GfY3|J=BV~O!+2jo-8eynXbiZgH7i5`A~fBhvL`hQ8CXcj1e*!1H<eC*esOct1kbg;l&=QTytk|a@*3LMp{RjyW50Fn^H@stoJ4#5Ic|Sn4Kd{BF$4;df$z-_B4*P&*m_tUZjpv^2#tRk#<rT3d&N*{R>7`$9<f%6(YFsKf1k_UEQ0+e4TcveaBGcsX%=~(J9}#Pe|cc*ejHx-H>O%w0d8y$KYTskJpQpoXJ*y+Wo_XZBh|?l6P|z$tRPaax|}tB8$P4Wnjx#7(`I%-&?dqqWDEn*6p4U&q~Q={-t}>j&#hQYb)#fnqeJFOR|#4Vyg2u!8n7_*Tk@bMRrxGgr^ZWt18sa5j*7pS~8r~+S$O%JP(OZY_L2ducJLSuQ6cWCs^r_AKvB{Ziw>1RfH;X$2oP~pRT5plu$@uv<fJ*HWEOT{4U1^7=7mJI1a?MWF(<%<<As55XBe{55$GUWQ-EDM~u?ks=FrkpWk3Pnei|ODLP{%`cvRDR>2QNu(8aKl#v%Y>y}#|EP>3NPSSq$jDYfT{@lZJSeE0kdIrc!Ix}`*%KXHzi9;y*C)5m}njA?PqbY~m&#?C&{V>c}5sj(;?a%{3G)|{8i{ylMTs;FVlL+av-M7uyab5=vMn_Yw;=dKTAw^!9=M^7^G9UHFfm!ImoPI}mk7VEDv>fv;yBM%v#it;HS)VJO|C=mDNF#b&@Y1NFA9gJXS=qRFh8!~$Cfmzs7V;GkHhcb1<dXIJNW4CT9Hp|1X6TsODGNskR?_$_9S+XRXXJtRT|uVPe=npot(PuqxNrDf<Hax6;wA)h0BNR~r*4{gdUnK+_B{+3!m{}}Xh<k*$)W>>?9mJ;Wce2a3F%=v4ko^djcwwe86gC1DEp(@!L(03N7$kJqJi`dy(3=7?Fb+b(80U!cxxy#$A6)SA2?MHClVh=FsM6$(-K0hjYuA)8!kqS8F$IS)Ubn_UA}*c18lI22z)LVureI^h~URL-syy~=s*OR0VFh&Sn_KOr60PQ;B*BhUK`eQ!sqRoraIvTD9{0wH6j1PCsuGoyz>-!R0m6fC>^U!Aa(-S&IE~+gLM#J9O-U(QY(!r2<gY~h9)|3gpHjKVU6}0OPZJu!(DuXjj+dZJOSMA9y_fKd$m30UW+IgLtESI6Aw-WOK???1G7oo`Y7XZH0P!W6(-t+Z3nhLFYX~+YIl9)Z;B28Ax)Nlo~Wby*w0GO0{*>4j((LvE;~|r*UgdM>as5;vB`Smzlz?ErIAuJ7IINolv$BV;AmZ_3k@T}m`KIxsg@3sn7e;O9;i&s@b#%1edLi2MMwZaW`})!9Q<o0n=V*Ov9G0Q<~e*M_q}PmxE)!d88|dc{d*%zP(%r<T$0V1Evz>GrtPN=WIu&bsK(*<1Gz31ZL#9YguUp|YA#u!&q67}->Jh?2VBV>*}Uwbo0mQ8wTl2NmEN6bJ&;Ir4T8J@xV7hBq+f|>LCuY;pQW>~!#ZJ)ow&!EP+@R(EpA-ew8hG_bvMp<aDv_5a1i*XMQ_}p2O4rI;p}O9Bk%iXdV?ak_6Q(D*g>{h340@9Z!k`WbjGYK8jIa2X@<UpR4cSj+TzKIZz{uuojTp>-b%+IJ%cl?uT|UTz;=tD=i2y?y_Z-+Bks>U0t4}JZPhW<WN5p<p*xhJJP9q6zO&X9^#QbsNEQJ8<qKC^*jR0;zP8{_TZx^B5pkOL4dwMr#jco*ow^}BB2(7{;(?6haN8*Sg`YuN#t7CS>0om*46F##?k;In%~p$5nVc@PSd;$habY?%Yl{m<FTiQ%dD^}D2jnf*@GN*(prPA9HY1<W!V9b5!MWrSgT4&IpZ13|-sA0aiY(xuog+Th2lgn|LG0dY!TnISff)iK=*on(@_6srRA6RQFa1%go5EiI$n?YE0mchA<0avF;WjUga_`cH{q3T)pbda<S#PopSK91%GY4ewcEs^L;#$Z};C1O;5J25$^fnp4S@wtph-KJR;Q1QP<Q1&02aMqm(5E3Ni{p1>$SsigL*MKhMOH_u@sUPJ1BrhRwaw%35t)b(>b_l<udAu5UXJi%Z$}q*BBS+>3r5{emRWz<Bh&O=hLrK)2U2Gp*zYnGfD-~RolNVH*&88Nhq9-?1QN>;9<J{NQRbkV?|Jiv505>sm%Mj%JooLU=Wdk`q{YiNhzyO+JM<(Q<Qb+k%AQfZ@hJMC+8&Sr-a-F5jPyZ)L>k}0at*eY4EPLFczwJ8b-(g>;Ygjy<wA{=#3#`a5GKE|BEBv_O*96+S+&Yas@7TUvM>n@Mwo;GrC(!*(?H<}B`6pA2n&Fxo?g!LZfF@8?1>N+0EM=K(A}WifYYcZ{JyG`<!ZmqfK~wm$?+b=5ozGC5HK!=`Da4}+FvD)L15-I0BV!?RfZjskmYS3g5*>f?u~>0<y@H;)8P*Ouxez$V`n}IPmtWF(YS!{;sdrYU>_>3fqN3%Zgfvx>z_GQJzwdby8p46gzRpd_~w~|sk4horPiUx3*YS9zs(!COuxlkeZU}+&ut+ChOW{*zqKi$vzt){isFS?4d6}|S782JnTJCTKBtX8RwF(PG78HM48%`jD@f!KMm*dPcg-u2T0}KWpLaJ0oc`~yU^#TbGPLlmK4dSM@R<q6?QIQxhMW`pcViZD#u-ef7Kv1Tu=E3{0-)d&LA+DnCp!;OX-|gzS-Ht6L1yZ)OFMH{<%V#B8fCJ=oL1*^R?^GTZTj&Cj6~W&0Y?i_UY~)jwR!1lN9CP2s}7bI<k1zutI0gWIOyCD<fAEfWRqobCv&m{oz`+9YS8_9DJ`6q%4yTJb+e0}=9Y$$mX`XFj&%)bH!O;k(;!j|Oqa+)^Z{G=AopcPEshq4c$iT2cgUcm%WTc^61Tf3?uYls=Mf$<ss{wBvclg!Xg-72P_nyt+~9=dt~`RE&wF!z-VXF#)8hk@;LGfB32+T^MEJXa+pP*@p|_WiuV<cBjZ}G^k%BWx64sQrXeZgd8hS~V!i4naVJjby4jsa#$RK5`wI_y?MUo^u(y|V~`sq^6C?q@}Vh^Z1_}+peoKXr8t6&j(>`ha$lQs0kPqXg*^D)blldFqX9p(%A@_hllOVgI-6xjD03CU7yl9XvL8u*UQ<1ABgd=~I`^Lf}yH0T3P+kvkBVI1wdEMx2nxxX~$&3&Ms0A=3Jo&Krx^JiG*mrdxYjy%_n1$fz}Fpr$KEoq#>FO1aCy1Hc^G4CoxMr*c{oKD3BI-SnLaKLVTH;&&=+;>48+LP%==-)@`eMvNw@UyUNldN~oG%3ceGmA=<yreoQDXBu1Q-mxh8)??FSS~W_HMDHuD@6egk_omLh0oUuzB1H^Q%Xj`mf8ksQXzc}gwG==B86ghce-@-B_$@w(ga@e)WYj{$@TTA>eiW<43cdNQOLr`Xb9j$J{Q{)D3obv)AEmMO|2E<WX`<R!mNE;{ALSdG4jqR7BESFbjO7uSs#*4A#C!-$K<#k<tpv_DU~R#0mu!@{D_F4BwNkc&3*dXh>$7uLdtSeqN8vM)tX{$Rt^gCU8jCngy&F&C~eV)r)3|`NQxuPaV_T??j9Su!@BU45oxN@%ajA};U*cmh22%~aJWVf<)q()p-*e<vk5@_rVB>8#&;HpGwmFmNuy33_)zC6Hot=0Cv0rRt+lYQl`?H{RU56Gm$Z6<0vQ&lB~0)if({D<D-?&7fp#Y5o?Qh#M+4y@EnLy`Ja*Ibs8E4BAJMHbPGD1B^#{XxGb-?jP=SlaY+d5ERz@xG5*2vJ%Z^=McDybxn}82r0Ri~Xv5mWS_ZISOWmC=<qx}vji{5>{M<y;#es&@Kl0JXvF1H446V><1ATzRWyZ`8)=ifhR`wh{j9?$8<sy(0-HF(wq7XZ)#v;hx5Y5@T9F^^8?1@jIO+hkhZW7$6qr;Kp!KprJ_xUS0=25eW4ktcGWbsiGt!yz!jN&~PCFxMxm_k>aAyQ#{DO~8C@_1<UW<B&<@l_m%Gq#~m`WqE1V`Urng11=_atF0CaoA{X*C^JLVwcS3c_&j{5OcY09;$+ZDzt}xDyM7Gvd1`zTQj}p)zu815n%El`Zt<8iP|4<orTD@1)=BpG2P8rVF)@VEI2qa-V|!_t9kso=vY(efU)@63>649qz{wgKlJ<w;m!lD9q%)VR+No=|<$B$)uU7{BSrNWpUbWBI|8Lvu=l#wE>OHkxzw}Fxn*rg~9&k%L3@7@Rgz=i7(UaL`g_VEAxfH=#mC1s{1shDluw^zAcYT~uOxlF;tgJM%@qSim$P#_li2rGs70b>g8NrDSD5POa>>(ApVL<oOD@_H^{9o(9U#h)Uhg_#iHix(BFoFPk?J)EtnS2NgEW@547+bc_yTWK(!G9fl{ju-$$NTr<$@jq8(QGyQ3gYWM-(UMG1oTw^1BmV+*!@#Hhm9dddjyBAc7{bJ$VxDtholVTV4Nnx9H-EQkAoX8?6-gvrcKW{R8!U(XDdB#7?<QOs80d(O!xf@d<QAUkDz`NJ`4#xebVSjdAJm!@=!BFQq^mVR;5)5@K1C&mIq3LEqYq?q|*<*mJa=|GCQz6dG9~llZ3q=yGXQmCHX&~Yu0dQS{yVz9lM8`BZ2S}(hZT`vM0m!o~&#h*#Z0pvVR>x>k-rzt;pdsn@VQ)k`MYssI}TXtK`^JG`7AxADH`L<!Mqh)`NF0gpj*naarl5p2Da>m=?f@CIhR%43mGv3s&_oDtHv@d8DPQj`K5?^qzm{E8#I*eKWD&an!Sad+7(ACVYz>FyQaQh-4hoJXxakoXBtT@qLn$FOc$}0R3s~il}>sT9Dk-b)acLcJ^nU`(%8qlO4)rjZ(lSCG&ko8WtNtCT|K1zv&MU{V}<>`vBC3feif{j-}&z*wp5lT1T6^Elx85O$e}$XH_gUI4(G~jYaucmB=F_AQ{8=8*?grf+haLZ5GJr(=#zJeV3`Aanl^mMygpL_Bfcgn;+T!iDUf7*uMv3Gv4=HcduFLwP9KgHwt}=e|tuv66>;?)gcd#6S5qU)|?|dxF~3jjedL=ecRQOKVC7Dh;3G#vLU&&uh^H$jzRBPzRuPi_%zm>B*p7l&B@;rQsSYzOLw2a4UZ2MKA;XGhW(#B<ZqQ?1!VFTIpEAX49M-ed-2_qR=GySF(t@j%0I56cVu4c$`C-C0|=u4C#>#AdKS7mVI~l&OtUr_KrfPj?FrBx@Pdn7pE4|f!J(v`xKn@EZerwn?nPev`toHMQJf)v%)J+6-o0u#k3*=J<~(s8hBp*?l}!C8`YQ<YiLv{W`GnOVX_E=oyVhYi@hA)@JQ+?5rZtjB<xgyT;+1i&Tlzhb#%xD4Oe1<Vkh(NfK+03J8xeb(7>Y3m3=3#VRBRY<>zjmMky>>5#cOg1@=k&1^`|an>Tbs34fNYg3hNBrM`>r~Abd2X%-EruNP!cOOeOyZX{H-ON)9Ul$XwgNPP4-bvnDCr-dsnDghV;7B)S7wdQIuzdxA2P7k3aYET+xQif}SnKXesIvj?2FuDf>4$x8|`f5NbuN^sx~#Oc85B&QbKP7V*)&xM^UFiM@n4ZaT=7@HcSQ;~zZBEB%k`@nrY<w>>!+r{mKc9RR(w|Uz-^=%90Q*o<wKbx@Sx^mAQ>LNvF86bfjBLB78{8}wvu}j}s%qN<YPE06}#vyYv@F`1IiQ~6Dg-J`wlvv~=kmz>KPzvZg5A$i{c}Q4>Bb@_@xFb6oiZ6{aT~E#&zs+&uP9Mj=53e!b*LkI5^*Vo>=aMTAp^qHsJ>TPlZasDlyf&M^H}xqPb@AFj?Dtr!BWUV^mL)ups~l9b33i1u<)a;sXn9=NQBTuqxx_dxaNiuw^TI7!PICf|p(qLa{Uv?+6eBa!wiS&;2cm#&4x-INR|2A-tPo&57^84L2uyRoiBN9_*zK5y`FLuxZSHx7{AuJD&Qs@g<U?CC=g418c?9PKCv$Qvn&?x8vBbQXyl&-b<Pq}>*CBr_IzLyPC!|w#MAl0Ya}toPb8m7db8=6L_?`fzhygZnafDjQ(jpIfKMo|B=5`Qsn+<j5zul8>{SBW>?TBJO9LEhXeG0U%{?S!_Sc&SA;D_@Sp4JIjo^sBv$~pV_yuf$O*o2_RraWtGBrNEsADg9P6X}LC2Q?&{apt}MSnU(X*BH~ya|#O+6CC5EIKE18ygWL|`xkV10uk-0i)i^Q8Sr?);>$FYQ$8((VlpTX>-?lK6PrG$NC0#zpFs*4i#p<XKH{(wl;Qnj1#D=Os-yTPO35wi-T2Fw<z1+iWnM^VUpZVluXzxAlDiZOCkA1wS|nfv2FsW&1yXNh3_?T!H%yp<NaLwWsjNt60ZC>Ds(=$Jz=Q(f)s?)P-2|IApWGgM0Q1g1w7d+zUe2S+FPm+K{Hb=CV1JcM9#q~9d}Ka$*9g1nMox}ZcHtCK6(rUHV2`_wf&+sWhn@BmEa<w>X&542UPTC+%p{NlF9#c4t<e9@G}`DMr4l3Z3kZRflzCl$ffug!KVNXtfh1@;wa!yg2)H3Fyz7g>h!s~ZDCmwg?F1XPA>;IdKwp!e+_U~^s52*&(seTwisv>z^fo_WP%RSEt<yK7_1DfShgA<xu2A4+(~otbALjfG-b`6L)hm-g{Lw2<!)+(Muxj&!o&vTkeVg!UtAj*S0`KS~u%8jmjiFZP+f#F<lI>J@D&){L&x#-vbdi1ayhs5-vP|;v1f13iF*t%%kWKga_Mvl^ZS8Yma5Q)ks@5A4a@p)v>f0*&HnF<0$i6)-`9*CYPbl=49jf=9zXt1s2(8IjljFvqL9tL9!K?vN_ytl+X4fy<!&j*BY$jaShVXGqt+WO=+adTzXRrlFzHp_>Mnfahv4xM#yF}45#onPyM7qrd@m#^OV<`%CE%&p>Q~P;MC5+1lI(-43S@ZBl=Tw>*b{U2@qtmdsA%xUY*VfZ6`0`ruzL4rQhq2Th#*%Uv>#q@;b5LXtFzxFzToK4=>;O(<hi<~m*6f)+11VBi-wQZ;Zym?b#LKgZ*R{`0>-v{CkwuC=FI?fmmLpjdz8UFdt@t_vfA((m!(G$K&z}2yli$VlcX8JTb@RU)6X9Dtat=-0p7k8?hZx__^zn-s6ol)caxz1?QUIN01P7UM?v7j<&I>I<^`K`lL+NtR_jxXjzyZ26LMV(<h5Pj&2BU-_7JbIJ>CLxo=%GWZFk2&+TqU1cEEOzyF109W=zP)d451I8{m4k5D-SxX4X%9HadaOW>A<U<c@^iIl+-13XWJ3Hc%`@H?a)ahAuo-D!jelG+*5-lNGl+iI5{1QlwH{7{X-LD5iQ2$B^^ym@CI+(+;r;6k&V;Rpco_AQB{k#fSQNy)V9&+87(sQz>}BKP3ca|ZfT{l>EJdaT3CaJK<eCYu*=r48-Bp)v=Q$`#!HcYYcXxQo-J>)^6FaLhTPtc*v8|>&|MWW$I}TS=(>m}rxD%nL+_g`*QQt!GE`R9E^xN3_<s2A)Gv#B$9z8^R-9w$+4sh;LQ~ltPPps!E%G%G^xYhgMl%u|nC4fN|Lqx_7KrG`89&&e!5Z1aV_F>^XOpCPwb-CxIw<BGmeMOXIU@`ud3zw4BH@VvSwS8<ZsgVAkl}q0(rLUsh0hpBi5N9K)`*6P=-dnWI48#8kTUR!pkHxYKz7>Wp*A=Q*aKpqZdlncCpI^nDZPU0wet?w7^C5SH(cQd;KAty9E)+on+y*(U*+0=&->NdCGSKoc@KCHL}M0*dLIbTY>lH3k<a8O+`)x?i_{N!GKN9H6YjoX^ppor2S!jL54hpU+?%}ZpooVvp39W<krZ_o7N;rd9)_}b(b$*d&_7R=jJC2dW~nkSU~rHDwQ~#I^L8F7ANSSI5zkls_6Y4vIE6g+S7v4G1B#e=5*B@aB}@B4N9fY=f+xK48>zJX9A<;;3bw`z?md4JPKXJ|I05&;YRuQkYeiY#BluHPnHw6&h^$#0VA3-_`uBWa{anhiJ(vDELwjM5OE|_wt$o~c8h0u-i%kQAO4>{GQ>bWo0pv2$p0FoRjuoeJO_ffK6wS#-X<Y<up-r-f8)TQtzPDaxgvWWIrOb)6G9s-~a%@xS3bK`M{q`+Va@such>qhNouO$)tY$3F+!6p|8O)`!qRuvVbsTMJ7l;NgwJHEOVe-gkU6M*Vm=W`eN{BK_rYnI0Mvs|8GfGf9iDa2%2rWq|j&HIXK)ju&*`(1@XTWHF=`Qe^IXR^E^GE1`*`yz+H6L60gW~Lb!w)&E9=pS8=s_TlC&F+DA^^yohI$2)fn03UXPZVvvxFC65$Zin_WxS3LZ`Qy{4|-zB+p>qM#LjP4)*QLIu*$C4V%xhwA-(6zY-|dM2ohmTAg5-Bny@~;MozkjWPM'
    '<!Snq-Bl;nDKXY)S%TA3hyhqgK98tH|cg=$%Uj~%Gorj|w*xA-1SbCth%W_7xGGTuXH0qy%GPwyS+&B~UA@yH|zAM;oUlt+%A=@cFunj4*dU*${Cyy<1?F3jm&t++s#}>g_PWFkO<ryG<IyxD6PQ0gNfI0(#Yv7AGp5YqID1Y*=L7T~WTFiILC<5nKpT3YI&LgxJv<>Msj(X&(eV$_Zk{3gpOWj!&FheGPqm_N#o22N-t+e`lXeT{+p72`=+ZVWGj^fn`^#p^95f-Yz0*>8UH8Lg)rV^)x*p$9Ck+XO2;m|>7y9M<wfFeHnY(^oLa8<8x%&JbJ_9S6jA$umn=1Z>R2{7Ug5iD6G&+#d9O^4hfe}q{RK#Ut`>>RtMKj8a4bPPOs{2!lWL;}ONA&{?w;K|g%k`9;vEe?4sf$}l)P}PVzV9-JCP2di1t<@3Ej1P$2#XZ7%T?*s95_DY{?9{SUM5%MR1^jN>3S5@DEkv_xt-~_qY4}5_QXWE_C`y$}3F!1Ffr5ZR7#1ZbOSqJSE|JUpG`<NA+B9y!Qxz5n2uYb3AL1{T<KoB#k#gl-fWM=_FeOr+;7pPDYysmy^Q?zo2JPxk%zFizw~pqmoUif9e4T8<d7h$L*qeUP`M`Zu{ZY*P%vNus@<4T`a=OiO`ipL6Q5%R;rKA4=F)j}WfNkCismA^o*7jM!H!^U%G`q~g2vO+V>VWROk`e$w>?YC8SpD2g)<3Y~Y@t9~E7YErIeRE3l?M=<bB@ln<29#z1oUuqOY&CP@n7Ttq%8rqF`dicA^MpJGBBJ0FFkT8^nR%#vQoB$-?nSm6-3DWjU3w+>G$UT*)8r5956T<4#^JWaU+Mndla^!o`CYKpTi<s1~M2Dz+evwn<1#YR6rpE3UsTmTNExN%XkOMU&@?rG5CeuvkuTMDM^hh1zK7K`*FAt{w5)G>-m$Nh>Ue}9u-$<e&BrBlIYzS_q{pIBmKeWVmqdJQjKmSYdvR@U<(oYrOh8)R~wAfIxmV&@6WaV^mhJ&=iKo=1n6+WemT8!zr1(<?8^}}0@hJSy4Uo^8Bb9onZWhR2k<nc@Ezb?(3`TG-i*WF-h3E&_$e1$Rje3!9oi|Bd)_XrD8#rd!9mc8VXWEcO@R4RNcsAyN>%C~?<{@l))UCZ10J&<xL-fvhrlneUG1zD066$_QnMVprBt!PjUXI>Sv(?z8^5QxFE4t%E_b6q+!pSd(p?;UR!HB9$E*TubD`b1n7rCNEvexX?0Sjv>X@?>?Ft*axu19Or1HQ~czM*tY;<o=jo&Z7fA{Rr9SP@4!re2$(QjS4o)lo})}@Lr?N80WWh$k}rKd60T~q<3I+eP3Vw4J%DwYBmdg)Sul3$ci2DDL%2}{mxl@Kaq-c>47cP=F=<wdD1N_ABN33Tf@D&?t^c@4|eJeR_daQD)ggkeup$%zu}K5<bBi<0O4YE_E5gwQ0=uf0<@Pf<mf4JvM?a6W_wL_gS5+nNF<5Jg&<&%JrS-@@b&=@oD`*e=`N)hVh-!OGCN6SN5mxluYH>GS64DXUX>nCR@j4}L$Y``teElsD#zziZ~t@$gFXC*GJp{)?DDEa%HYi8EV2&`<>fnT7l9A4@(&%)k1X&p#5U7R3h<U-WFg1pHP0girAcDNtksHEC%W*X`{RIxsC57K>Ioqr;n%Relv>?PLx|ih&E&h%2Xw0#+d-KS55gW(&(pYbPf$C52l3dy7+jgz?*(zqTFjr_K?=W}u`1e;>e<YI$1zyz`YL&J(@LMtUePNhS3$``-6gVtKiUtu2YQ$GUD?az(!>Op@Iy&!CsF`Ix7e;}P%?)*k{B5<p=!`Wl<B^fv^rgA749!-7Idx-2D!`1NyXfMAJIKwzw7O94wQP}ca9F69Ao-@|B)$Jmm?09%96k42OU91Rww&`YsDt8yu;Qk5l-B{t92rDRL4$~fspEE|pA@N8d#8%cF|;6=|;$j`6=oR>z4l9F%uS=o6}SHPCY<Ttio&dXZW26)~6O0OG)Ir_6fz;Pjtj=^J36-s)mus4c&Ys6_3zLR1;8io9(B0ep1tI&MioM4H}&bBt}+sL)()rwpry^sRV+mh5q^WIe}a&J8)ZarnM4+cvjoR!c7c9|xE7TD5Xg!$B*n>D%>c~}^Ryk@@jTsBlN`kfnKZjvMN+&|sob_DeFdO!lxhh6z+!r9ygW7atVIa!IGqxm`?<Qy{+%uo!la|aAOxsctqX$+GkL|R!w*ac*k=lo}DmvZ+y3d?mwr!&%{uKI<2o`%u&g`?lw57Wj}41F#32%=A#{_5c!#A_Z7R@N_bCxghqREu?_4>-Z(alL>%Y@nD2VSpqJ$7sLOhk6z+jed+(m}}Ji`EwT@L0`%Kz?1r`=rgm)pQ!uFH4Q;bVb{FCJkdPyFi*m2e%v!pPRn)VX`xP_`^B8t!4pP<@RwV}BqHBefj^txW6Xb82bm1xw)P{NYYmTR@12J4aj}kq6g1t+vx!4s7_jwBn!^|9Fb4ML@z(6g=JwCZ2{LS&FHwtNEdRn9TR%AsE%U<p`2AU#(=7Pix>WP$DEaF^29{g=O;#R{)`7s)nUAsa<-DhV;+ih7gF;~;XqnFo+wXzx?h%}q2FPH;h8CV_!?aQ77-uHBu;TA*5EThuE!^J;3ay9YbRT=hU}(M5&P|8zd+a_y#{pY3`5BUEcDndT4rQt1cctM>$xf8!=TRWY5I9Q_eii@#BazY`K$z)aNcRY6;{x;rKd<ngKu~)CuR}j9ZU@AU6wL}_lCZ%0L3kR(cssdQYvI?)NxY40k307v3_xM^x#ynW<Un@)okyhh^<=RVX8GS8lkHpP*}cDC@@zLfJK=}C5-m<pWb=lO%~#kn;upwk@iI@3(jdx<GglA-w2=8s78BEND7R>G0P!NrJt`gE(w5=&QyJWtr!w02_A&ybHn{2l3_+lBk1`KpFeqn;z>@~JH5d$IdBD4^$_?UeRStPwZsD*p;1S7kWs2@9pFVsM47V_24Otq3evJhs-F@&l1Oh;QZ{{~5B3MFQ`l$MW8?<TY>Z_JV2mze-81M_ti5ATTb3)V`%MmdjfT1;>dbb(b-Tg$-ya2UMil&BX)Xc+d?$P7Dd?7QY`CuHWUzCjB=61i05~E>}iwF@mAMNNo!1Amscry8Zbar(pLmvovlgvQ~9q@3I7oOsLMi^j@v3tMWElLdX%)ZE9Ai+>pMEA%XzM=3=<WjY;c9D@Y^~XTit&rm0=r&oP^dY%v@6cTtPY83DRfH2n{fy!>MG${pfUadka`_yN)Z!Qc7NIbX8p+ST&k6cO1Z;8gnXBj6=rH$wR`*%<8~#LuoIe<}Kh&Ii(45aGcP~%3a4D~2?<x2WfxuT8<y@umS+wQ-Dq&!S?)(I3mf6BZD=_BHN_Fyg+I*+UA$Y_4$t`?+Mf^+o-xwP4R~^OI#(x#Siikc4dhCTA7mGnBL@2$P8@IP9w^||EB(o9nfl<epju61x5AU+vor$}s?y<}9ns%-ZuP3n09b8TX+r|jW!=W~XAUL&~Aj-Vozk6`^yA0IzJS;j$3iT_Duar7sRvJ<$v{!mg9`2;@FMS^8`wub$8Sw$JoF4{e^h-|@TS$o~^f&Awqdwf<LHGUl*7s+`#Yl*YGMrnKP#oG8Xn}BOB!rR&mbuqP-$6@Qga#8NG=*Jyb?#SP;Ah8<A*l%vdr|Csk8JyR>Lwr^z}<SRyjl)WEoA}ekxZTeswJ!NhcEqb7)5#i)$^s~?g_>@k*YCCBt{uREi!Em98=62Wa>mP56LMYil9&#uct+VK(v?@mF}EHJTh{E0E@XG@EFa=YxVVO=CuMcQ77WsN|db**CU_%yUs=;_k4=*)3qa?XKPAfO?4(K4?1x(KI2R&oHIrxB4Q0w27{(2!E7|xN+np$eYy2P6-RM<l(&I~t?<=gj#ff%4n0Iv5P_8ubF>Js_Kay%{^cg!1rD+W5BFv%p*1EP-vsX~(He!4Ca!#(3&_xm)=g~LJQN91V5~lcE@X|?$f%9dMqsiQj<$UX_+zk;6*;b%2xLT3Mm2vD%XkRAQPP#uo9-xqc9eSWj`I2Bgy#5wXHY<szZ1>TztS#w?L&x;4+GILc0|WWK;d3M6wRrZ@gO!?zWkY|k#T7aIxUg@C@`)G*OAC)dh2Cj7#+5y)T+G#agJ#jAwHwp4X)rhD)FFTh|dHau52PX$M)FeAoXp8^Z0-urw_!Sewq)Mzv3qXe{nhB6V@X#gU6$S<pyaYntl#U&FY!KRJetbjM*|`7*<zBAI6`uGT}a+aSJ}H{uCIc&_7RKEb0HDeNV+ohMASLjxHLeX2CkYq>XFVd5!lc+DGPJ$O<#$_m9l`28HK|z|8p>hs68|4~eB38tT$3&~n0q+~}`i5T5}L^2<6}J<6kD$Ax_PQ4?_?IhrjaEglEe04I)tYTW6Dh;%NZpk{HrcB`Pfuay!yqzrY;G{EEfDiR$s1%(lrTvq6iVMd3HGSqpjLgY?h3O%AZAa}(rFogw1Bt$6-6s7D=MMB(&=qghub(b$olM`_vDGegp7>fF`K#C-!(KAFt|9p0mxO3$_L4H<{fI%ZhN+jZk;h}Tg<163r_}cLFisZ?oJ-q_uXXSY#4TzQ9z-&le7M?zc9C>tz#_j0+$WLog%BqxxQ!)5%txG);)3CD(6&=Px;Zo#M89qI|G@?4G(hx2*FRmeOh#5sIT&h!vOn<JI2t!f?r5HUTN89l4Mfg1N$e|C`qcv@;dwlPt<%u@^jLPSV&nfKcqy*v#+@lilkUz1Q(~B9sp2->$IvS^D=m$HKo$^KF8GI(F!nB^bbz|n18#~_8qr%*70kN8tInBXfN>XT{K+&B+1-F$ZhK;NfvZPU;dZqT1f0TC_lle-D$dbVc;4W~4s>&lj82h3)J1S(bxQ9rJsMJNJEJkrhKuJ)i*c@e=+Cw1%NY@5k_9TqcIs8WC0#Gu7E<)v_voTUR0ZdBOaR7&fWFZCe22f*#XIE_ly7BQ~D;l<d9;fG32IJx=3S-i2=)6=OkvxOqgYyl*NjAbFpvf~D5in<c+ys6r#?wf-VCNp!vL6qm-%?$2_OGX4DNDOMp?geSOO6_I1#z(gfD0_uEgAssH#g?feyEfJa~S6f!*GzNtIqe$gRpzP==+;_hwX{C088r(#X`W71YDYUy<Gv8UF0jB@t%BEE?v)``y65XmUrg_Kq(<T-nV}~RX^>@35fCl^e7z6N#6<fDDR<11M{SJT6z{eiV#v}Z$3_sMZtS>P9E(E^6Y}ZAX!ByokU6uf=z&w=v5KWtD@pdy?05e-JV_gRIQ&%1WkEDQ^FJX@F)HdJmm}!^p<Ls_sbz%tFJG2&-^{LYX=^~2xLUE=OiidqJ$APFa~_3!0wg3nH`-vJRS1_9rU6oB_|zOZ7DBGMS(WzQeho5wJK3dQ=ry+Q6hPeEG6oVOu&O&TCEZ=>i+%pzV<Hr#wW<{+OG*Z^Ncg_jQx`wo)lIk*uqq)$kLQlQSzeHO{Y89<7TO&;?&JjkL>}aI+X&TvYHb3@cBgvMF<<EnCFsnTO|U~oOi-Rvz1GEQ7Vg4U6s<Jl+k!al*phZ)~QrO56q-XUX-3lx{_JWf~B}9g*un~qU2VkxF`i(A~?+>@@7ZNn+asLIFmC*qhUkUDB!5G2nQKS^MKm<DS<y20`=OZjfZ>j@FLqR-b3QbRT)dR7~;--<wdA;_LTf13(dYM!AKjDj7fsAb<#{XPKfe8S0oH`NQ<{TF?`p|%HdA*>a)^)H7n_0#3B~~@+g^@C?JEXG0hYHkAi>r<7dn1)NI@%Pq{kF@1EVoAhS(DZ>$WnsCG{6wer6><d}c5A*XZJnNWHy#wjoZnbmuoFvk`9t$jEpkerfpDdX8>0=8r+SPoYI5mqdJbY$EYRDhwy@wk}B7z>N<E#y!U#&d7}R;J*eIwxpQ$t@i}sodcGOQ>}TQz--042D)Ffw83yWl`YMum{eGcBt=<wcF7RLyuAv2D)K~aD-@B9Lpdr@<Nc1TJg<hDBeWk@>8@chLKb`K06v%Nsbz3;U%9aPkZ1d>lDpQs`e0W^oYd&c!0&4CUxfa$Eh;P))>u2%D_#zpdV3T6iHc*t8!^&Po|@w2JU54-d`yfE=Pfw-|mPIo15j#<*Le#*_SNjq_Uhg%Tb6<qJa74G5S;9fI{DZ!cddr=4O4AtnzNDtP8BHo9t`z3WD%Tggm!ITx0M0F^8XMPM2%zuNV_CZRW+sCW%CGf2KB^Gpuo5!?Ve+UAz1p5ur{)zw#PAo3;6LFZ649=MCr27aQ_cM8S2Q4A`NO-CIms3)#B-dbsuV>&T07>+6znxt$ZD=_Jba8ac#Y@um{<L_-H}g}{ERPuhIGV3Zk;qlotjmZ6(XXZ=dhNYHIw&+l08%Re_s_%j5Jhh_gT;;Rl(y8w#mdm6}$QBHi?eIoZa7g}B|<Bj!b|GY#z-R~Vph^Ny!<NjGA$!SDcH$o%#1Ix|+P!rP5?*-DSgj^NaZ_<`Q8$5|TJ6LZRD(FT`g*wGl$O`#%vCbyDwQS&ivVqji3j-tMAuVrd4IyWw!#SJ@o^QcSc2E9%?8cE35~_r9M}fs%iuL`my7CJ7v`+LN1OO?_Smjsp#Peqyu$^Dcn`lGARLN)R`Ey#UCi%#ewxEU8zBX{r+QlSsk~cw$BC<t8jq+%bQ0;nvb+R&r<PY;_mQN%8Y~Ig`+0QmyLE<7Lz<plN210tvK5_%HeP0aVxD~>CD}T|pM+m9Y{8<3CxfQZIA%L>`U6G+T);Xw~Mr^^A_p!A<p?NA0QUUmAJ1mHtX9d1@BM|A@9*vPw7yH>wBw4ku6@w7Gja)y6IO*@<XV)O@8ubV|dj)Ont^|j#W0eq&NLh`qF#(uDR54n?t0Ja)ftboa@2E3j`sw{Rl<jh6i{xK2fN5R!yVp`AmiZG1uJW}JRBbDvH$<SZ<W@c51deRPaP6rBtD-6DtD&g&#nK>DJJQ*QfLp_r^rg=gNUINhrkq{@pXiQ>`YrSP@EXs5)=aNgXL?6nMM$$_kXnwIcps|Ff_f1N!;3uuk=Od9%3K~V)e%zhmc3kM`Ceq!?$Zxwtix8RJ*zvA4b;^Rxi$!V!(;6dzg`~S>+cdu7`soy_s>us==RHUi-Wo-H#B=J2U*Tsj;;6cl@phNbRz<*lYm|*6%=Zb(Fq5Mz&bXf)Hb5y@gDH8pamV*;9@`v8^OmkT;(UWgW6>S<EcF%g7F+738TMy;KPG5EF-@GWj`^{o;3*ffTRf|)|u7b$191jm4JAf`;f*d=1(H!c-hXkIKn7Zl8bzCE@6Se0Ym_C3v+CPSIgRVe;~5XXIc~P#K6j{xSj&CcB6xC<<@+0D}QlpnP<pGzQL%O1JvY!m+*CPOQI_#m0&$0MVv^tOgA6$=^sVduL%g<rEu&hi^GE~B=Kv;$aD%FGYOCwXHxmoITbg1we<QE=N8KL>l=yNL0>8+=$BXhHbNT2>o>l$Rdf2fUFJ7Nb8AdP**z(o?ly~Md+b=Y4{wEK`*K9v^m0VoBOD<vg@HH*nnD!x38(^ab!(hlcRjlfS0tS*J(6<cff*&bZ81o<8$37>AO%NgQn(NBXcE^JgHALf3}aBqR#wW2ilQxx5;7^M2)Sg}OZbbz`$(K@wrDRMTtpzer$A^=7=ntU_@dq&wdkP(ObjL=lLvl^Xq%J*f!q-^18S#-H3rM>SZl^|1~$nejv@udeyGBpl2LL8uHCt5A}{HO6_VU@@^Gi-@3o%$T(n%@Pow_z(Q*}HZbEPB)V-<i@1*A-=Dywi6>{#=U;X$;KlqEE91aMc3jyQ1mCpzl$MLXeWfAvEM+1mCjF>2qN{C~U7p27dp=Bv@oP(+Z0<;zLh-aS?@Mw?%A%qZq3fwQ;EJZA($kKc&J<*aq(~_n2UL3E6zIG9sH;nMi$IG^N;TX=NI|*a77_d=R<gx}$Tob|^F2y%3VaGz)6;MG{E+tbc?7HZUw}&Z3GT7%*c=b}bQi|l40#-d-LcgLYT_-Zfy@F}>h|8deSu4m#W_Sblas2xr<husEwX0=&U;tlXB2^JMxI&zQ8%l_<JD)%nk_MNM*dAfPyE}6CG;ZkGso)}o56_5I96A|=m5>-5DU&63GA7ynrWtn9_QO(g{<@{0Ehx2BWmm)1M6@kAP>~?^tp|cJl~BsEE``@BC0kNSrc$By0lGiTb&`;XBR3j0B~<kk<T4M;5f^s;aNYUC!G@yDIY<qX1F6Le%z61K5~3n;UKvh{^ZZKlKMj)Q^N_7Yp8w%WU_cR62eFq2NYAm$w~h!776om$&K*teN+-xjXD)%m%Gh5gDMAqul|`vuEA3qm6tReBe_X5xu{QlrT`5!<`8(+nB2UA)sKaa@A'
    '&$l5EAGYW%5fNX4u@Bs+mV>sb4GWIgke0uI^fO{--VPN_%skada>^pMgN$}3sTI?b!BS4Dv8b%rmaE?svuOUt2CE^3*52gOoto;CztGys3DkMpiohfge`Lk*Geelu9W3*QSAFcIU12<?Jvnmwyp9ruJSL5-@}N`#S>W%#N<XQtvEk+)*)#JqA<p7f8fuyL@vl(htp5{Ttd9>gNM<+6aYfo#t4c6t#M8_q6XdkFG}P^JRe1}!VvfWG-)J80a8L8Pk12m=Z~j{ue$67>5RfQNdmKx>q=e2$sAVxS~2NFzD{2d`QnnV=>Nebao}T}a6s;L^v(DMk;8%|&<<cM>OmqCZIVebN32d%r4r?FI+=rY@l<lmQ!^wzm+)XA$*VUY3+Mpq0s`(0%GFDV%RW$F8~Jj0B#SiCcr-6Kx>Z_~a0`EGQ%@mGU=tvW_=g0{-K79WnoLlEB%vN7m03nradCJUjWf$q%7~9vrQ}Hn8pMCVb0-jKBj=595MR}I)MfvHfo&g<#3x)?M=bjzigJ#Q$KBHzjTP)DD=Y!$P>D+TZ;#fA!tTJ*3U4SAd#h4Jx4eLn|3rc~`Ft>XU~vGu(+dxLFkmSjneOb^)*=eOS40bt@C9`$y{<^bl-5!lZWY;SJB~R)_Ol!*PGK0Z_6mClvG)VgpC(EhVVp8S$7bG9tmKACNR%?10z|!j3Q=vjTFQ5cY7@E_qNp}%DFyGy@5+nV5{+w6KG-^50F1HkV;oUzJjA8_tQ)h?6`>F^lhWm<MF^R;g#b?^H#k>uZvAWoMN#_ITR{=?-G9ff$*#NJI$Y612m!*-3_7aLMFPjbI;v`f^2n*i4M6Hom5b#l<JVCHg%kF}3AB%aK|Hc>DFAVE7wTkCyk#))hur7!>yekPL>EzTt6YI9B2wPK2vNR=u1fiF!0iTLIw=POa>~ItJQR!~Wa9RLG@9ZvoG{|l2?IQunD%k4{W12RQSAUmhF#q@aQXY^0_yvyqK$AaJ8auE=^xBa3EJ$#u&3y(IB{nV`93JQYR_3;SgEG4DK-ssvOvW)sdDhuadjkztFuLxxXi;Qycxkpo81ZdC34VG0&7bI(MF@gLKZ54LAEH31q_=-Mnz1ZD20(ci6RYrq`AXulC(UYr1fVmWn+%SCQ43e7_B9OvQuCXsWJ(>9kXmLXvISSi=BrcdJat>(4b?OM&MZhVgy!Zijv~W_>eAZ5F?#fBd8%V)EH5C4A+uxyQv3Sm_mz~i@Zh(Nz`(y6`v8YGc_Rw;di#DQmyY#0Y|CKwaOwRU!@(ht_j#Bo>orG`ejX?ED)wcxcBMW5awV&jc|g|8X+)0py&ib*#u&oQB+b%d{jv-hprf{&pc7(K+)dg3T(`RzInFrkwUcUtmZq)`3tkVP`{z*>9V3Icmg@uR(y&_qm911fNX*S22r4$h+0=s!cZLnH}EimN|LEk;!<Q7aNq)Hh$9VQOp;avSsMOUz%Ul<Bwvt1gpA!4NNR_r3REM=Qi?Q#NVSznvYDy$Wc-;W6x_-hLD?lZTXO80#ihulEIpN+u+L_HA}7^LA}A-7JaP#sOl{wweT&(~uz7-Q{ilU)-)E`cBi+2C9H^BqJW`MkdJpG=kch3C8A$87pCnnfC{1<xSsKE+!5{`;)*_Hs%m>v;a4@0v2a{t6lLt4n8V?^I4&Zj6@CN5vG&O0FTurTR)x0`P=vvUVCuu1db?q!47?Z43^}s49PwN(0D`K{rTFAn~9>zNJEEfokG0C^bQy|ajxULC9+NmZaZgVXw7pW{eKPrc114ksMnpd%DyxgcnEi=mwZy&O(#ViTGFfh>Qh(+0qRa3)=F~?zQ^3a4sN3vKIx@#p1QI<`lmCq>Y_hLWxB7Pi|6PCm4l{cP6?Qy!DqWwiofoVE;@$&O~$u`K;p;f|Mt~`LRRIaMLe6CDm6$TH|jzSt~N~T}x7m(%o4W2Wx&zU3)`MnTV1YrUb<@yqMHbMhN=n;h`y<o(ma3iVg=Ykt#%z~;HVYgM7dg4A}%TAV0LL_sPfUl|?-oBh~mAx*P>*Xk@qbwJ}j1+!=7w+JpFxX=#LM&5QgBuwEBnUVsY4<JBcI8nC&x|eF(1QnBbSVg0RGgcrk(#eg&tx&j#r_{uU^K72Q6sJS%>C>)vLd?Q)~cw*-8D%~KD*lPH!7Po+e^AX(^f5*F_MAp?ARtb?nTXstmccFOKRUw%&>l&qI(~^d-sDAR8AN}1mUhzO_`op%>1PHk#8#dU|n{qx6`^DmgU$fGnTpEWVzl`wmasn^3MCm9py0qR4(hX&!QhT%2AZ7EGN<bbJ=Pbq@A-aOYYlR7qM3z#>zUPf!L*>c2$82;>AfI%AMMjmvc|7L0OKX95%|E^H9x6Nzs<&`rP^U4s-9``RU%hER3YQaOVnkk1R~bzB3M-V_rQtJ+EB07$<!5n2m>-V^4b_#;8&-P?Ye^O<0D~(jBE2UT|%~zP?DIsW0-}>#IUM(6u<#ywagvtA+QfMWPeBmRY%^K?QGY)McxtaF1;*R+c^5TA=+`KqdwSI2_n|-{{H`OS<avK%L}VV%e0`YPVQ#4-d!<J}@_kHVR4CP}SzE>ah4se(Z~@Y3^cw?Psf(L`}_?YcmVu;vH}{9`tOSJbS_%fcdL@M;?W|LG&xe{tI|EycCWAmLNiYh-i64egskaS;>u;n$YtHuqlfW^C1$hXQBmRu!V|5HNx0}4+o^mVOj^t>6);RDB_kup7CI>mpr-V#5E79xzmM6G_$3@7qDq`QdGLKm}N~UU@~*;LvC1PEoNDhOj%aS8*v8kYPa)>bMi{A;fME#s3~1v_ELDAos@uNiS9ks!XzCLy{ly<(bkGOYga8tN%B-~YFWuxiaOh?bFQSy0b-&{M0{PtIE({9uSu^%=WVxmVaYEmpu<na%m37r^Nut3hODBdn`iDI%5fn(nWWd%sq?pz$4qKd)_I~>0pnMm63nYhp;0++B#mlDc@raC2lpsiUmwMlqOZt;`Ep%eQIV=#C8TKz5kg{3x`M}ya^(u?^`|S@UWt4KZ2;1>E2BYmzT)O9B>h7(4?d5;l_IVT+vNF*(D{&_UufLAWx{+V$t$fvb-toBcVTtqX}(g_6+f=9Nd?Xrxyh*`&Gwa~uf!c!lyG;x!tq&wD?kr8X3yp;7@riR4i8=G@G#6`3N3^nv`Y#NA_;Z0FVgOcYvoF<a;-q8KrPx@=2{S-s=jzzt6UpBO|@uinQQ%~RP(l0xi%uKQZ3qA=31zL$%wN>*DBZAP0w75Xp*w1k-@50L~BuVx)!h0f~xr|HK%LwN{zHjnQiHqA(1slnx#LqnxzxSz?6hG%1t6D(L}WDnG>1=DSwWF*=6*%D&$-wUy<0|TCt&xS6Gr#Y)w423R%|8S`ccF^yzDv&n$jVEiP=3bxrqRR2ZqOQc6m|B~KR094MN{Cf>Y-g^A)Z^z3mOd5f7SjCcz??6K*Y?zX@vhPx+jKHaiZFlpIg!Ejf3Pb%9cq%=Y6E%MqjqpW59Ult$z44M9SnVy}R4cWt)0AgN&o(bXeJ@iaVmdh=*?VHfE_*u}ibSFKt)U8~hZutszThg;6EY3A`i;B7hjH$+UBgzNO&K{*JD$3+AsX3UH_QTjCW<6c?R~5;Wf7J9es6T3<i_^8Bm9nEf7?JrHkqXC6DqNpWg|FDY<$EaRmGmzAINfGRVXd@kQLa+Ll;-<nZ8KAqE#6jn(`N8q`@y`UZ;LKRI)-G=Qsp9~nMK;TVU%hH@KG>z#zNeisiP()0gs{sE5@e^X!Z{9U6rj|p@hIonTRp_u=5D8J&cg~iDfHxohoGt#u?11P|@Z+l7v?hfK9@aR>Tk%%Q;HPreLNJTpXQPhYt#uNLlPFapBBZixSxml4G^w4J1}3gW7I_)^<^LbQo<LXhrv0XpReP_UIE^Xv8FB$VuQd>?}L<f7NA@AjopeA+O3Ihs5PbWuGJKjPpC$H2zGLt8&57HWM;3xjmUi5icV<T?>McB(c3pWj$D<e^vX0wak_&{(7wl<1lGstF3HlsD&X#lDyl(qhZDCuTG|A;V*)b+>d8+RT)CODk73(r)z=Tl8f|llIA7S-;KI~jE;5fir6S9u~AU*ZsMv2kB>>#B;QVMQ1E!AGxW;S&X-jUJTJ5CN~*EXA3Z*%Wi3<+(1eYt>ewi2#g}!>ksuIjA_Q8rwQWbBsixWYt=i<2q-)n)o3s;@Fv$H6O({duG1}>fvyiWVJT!BBN=l<Tw4x96@=D|@+E9uEH4s}WW)ELcnoty|mem!%yn?7>PF-PR^H9W8gQB<+#g)icx=Mzkf?-&RD_6inbxg=4=BAjUP!!V?yjlC(Ojp>|x_}3%ypq)<US0uj(=$6Jf*<H3@3p}3h%4yco)rfglp}Z59&%xIr7W*FrSZ?}D{*n97?VWd<ww>XSFc#VK?;jWuH}EKv@)Jo5MdkYTC4`et*S68k`xC;Zn0bV%$S&nR%M1UZWFWY#HhMmnoKZ5Js{SL6g0#vEeRD<W&{L!%hNS2k|<l!i*Uua(oMn(Ev+bu_zI87v$&0~QkF9GPQoiPDnCfk8X4CPLJ^Wks>rsX3wl<YbWz)~iXl}A@m6prS-h|p!V>IR1TxmOHXHwJlfNMIAzh0CZbgh-P$pl*Luf@*Rfa}}Ptcr!upf$w7XTfhI<E?AqN;cQr1tx)c6hOi2PTb9D)4CER+Hs%-@ZNV&1LuA{8Lub{i4NxTx-+u&sh-@yD?D{s!P<<XoQsu!xL8*WpdFCf`t!ao+0~?gr%zRB@--zDvR3$X}Rqrw{4W1wbl(c!KI5~)YjP>w_JK2hJCl((Xy>uCUjsx5hRlaEEi#jRII}fa0b~he4c>fNbokrVA?KkIQ)b$#~eHPoVt?_Ap1wXSuNz;zDk)H1D6ddnW-GfY>&8uK*)w@2ui@RS^>Q%Yt3FZN}MTuUH#$fmfd#Ci!MvG)s6mPL`U7vvj63{xN&OE(>O{MpEIV4bvin=x#W2+J@mQ6KoXJ`%3Z)M7M|QHqOn$;nG{cfln7)FE$XNooC<IARr&48(J1AT+?<jww>fjLbB5?o-a~(s-}S5+6ei7HIe#aPG+da;jKU>53eTk|$bJ<&OxY+;LWPa8@#SAG3~``R5G+wK5n_D_t&n2!lQuTR6KW<0PCo?lyj4WOqel@bLx|1%td9%xSWCYvTlNc`rsQYD*RR;f_PG@7Tmqviy}zruB#w1T8eZn|5H3>hP(bP;oErrELrB-ka*)>Js|IXqeC1cl>U1YL04Zmc;{T)8CF=5$LaXxq)S}!hBhMhpkz)fmX&5k=9kwP2!hA!j^pq9L{2p!o95?2VSx9*)8{B7ClUHU4bzPR@*hFd!IV8$SjI|TAk;|coau$xLNja>_2<T)6B49{D=JJ3!Vy%HZ==Ou9Q~akievfqy$+fq<m#n^4*{|)OV%5rGiW2v*!AlF)d;0B)(AaXmTK1EoB~2t!1`G~)qb!YNl)+3{il6EZGE<F)U4vk3IU%K$m}(1WMh#xvSg70Ov{81J_%bX3D(*Ayz2fK-Dw9z)ifJKj(_#WAXwhkVE`_|@JXBxF%jw2t&4%Y&U(s}Wi{D8bJWkr$9)d8m6OJW;%{IzpbV>x1%0)PqoAUDfShmkxca)<lS7Vnb^*Hkx&5I4pGv2=5%toiAiSN}Sw^cCRHkaaRE-6?nBc9Sh@^m@vDBCewltnalFGF(|CO;uhWg+#FxOPHbJaa}~iOARGxZ#Sm!A$!dBqVO}Z(C>KEtaq>7iZkuzV2RmYX)z@5VpCLHh83{4SN?G1INE`5TQI%9}@$|Wsgw-OgU_p%SO4<J%d<lVYqV=7+8+-C{rd8m!Gy@wWUkYraWzUZiaaRyb%$YH48uIBmm>tswOJ!t#rtcmeJRHNtTl-M;U2Lgy9N|&x2ZQmK{ZT#xLt_oMlAk^?BcG7FeCjs0%SVc5ed%r!r&8Q8uVtX;B1SPP*)GrTJ?4W;)|8Mh%K&%l*~Q!tBora1%CGsn*!*=9w#QP?UP_*1zNH`3^Qj-+axN>V56!T0Fi6h~_@_>_fZwZ`;L=i{USqA3pkqnjeR?B}7wC_Tw=;@8x^#9v|C1x;^FP*O$T}w0jgH*<MVXAk2EDaW8a`h<0mIp&Aq>Ln6SP{G&H9H-4$L5dF+O`RF+L8LLEp9EKQGp9FB#Npt@1@LzkEfBhf-i~760&9HS>WJsGx7h$l%zEwciA<ZJSy&j9X;IjM7|7-p9^@jM;$K0njB`@iRVLEU<ea$v}lSV4IHc~y-3q~2F1$~ngiml~Y?R)VP+q-;gg!6=VNgt1geY4KYz-%_oyWeH;#A~xXsM(&Evt1GpFKl8a>LO=;>yuw-_Be>Xd?^g}E~qf23SpYG*|4%aL-0AoA@SJM0m+)32xc6SJVuf@dpt!GXA;Pvd0h)x*3dd^RjW?a$bVPX;OQg>@8OqYqFSUHyir96;C9|e_v=gQyD<>M0Hu&G_ojht;S0t~_ja{fU~uqQsngpn3)Moe;rS-yv8|C<PSmQdIZ^BG-Bb&zMq4GFzPMHg@f4&pR;&#|4DAenA1Z>jhT$?mW1J(aQy7$GQpf{EZ*%i&#5y)ZG2en$_M=A;0F*B&3zjvk<yoGBoVH#o0(qUwH5LDatn#It$)5UBMq4y~Zcyd4QO=@VM7hdxmF1Pw<}4{J_a0{!IudX7#Mp5~DDH}v<tI_jvK;r6i!EO!FqNa|=h*uY%|}}wk{x65d>TWVrTRzPp(}g2*O+ge@A;qqhYfsA-N1*0eB#-0%j80;IfcP`5nzl-9E}oVUREanuV@u+iyiJgJY-{&bgldr9?W~6yQTEHUEZk-OT60-E`_nCgF3QelwB1UBxv>dtck!;Z?oxN{`ZC^eXaf6a_rvFq+11V@+3Ja!iqaHYsOF}K+d<y!g**Iw{4ktT|u2+8D~kL_N}skTiq&e$?`@yGaCo1I~GwEu`;57g&XhAI<$S7^d!{bwtR;seak2eHR<1=(0vVD^2C-rGJJ{9F?kczFJzq~$3&b{a=UJ4Z?ko~FQQdDZ`b<&-?XF2aO6!NF9l$AhA0I5Q2E}H!=I!GN|qqfC?xRWEa4YvqV3|fQcogJo$8ZJvF()YM+Y^2M|kTXUA2VmIGzL&Sr+J{&o3|fTz0t6(;YDonRvJu3eN_cxVkrAuddVZ%6-4_to2lIN^~Xqe>zacB>F_m$h_I%(C0r-NAM>2fnd;qCEM2z-<!wrIgR3&9+j-yc27_a2F@I#-Bx<_Kd)r$QhT^gBjXH?-?qN`RR)|r5#THvcd{3JauPf^d$a+qjJ8UqUPnnDi&l(<s&~9tmDWl;+G+5#VsdoAPi~5FLQE%FD`1{C@}2+rs#S7PVZ7YV*^xDg`?YcS#o;6ZeAZc5nHg(*DHB($OZJkxPfpq+Nu}V>5~NklU$3R9CYfaI>ZPm^ygKs)?Ut)pUgJQdA^;1?BZUByXKdjloP{oF{1Dinr*Tu1-VB}-SfNy5UXN}W8WHS>0M2`aV^O)*9`eXBWMY*OWkQvh#l9*e<IP%D*v>^^ZC5qlg@TVQ_%qiYm34!cI`!-%1IK=El6!4)^H&;;=pkYb>Eoqv7<_~9$$j%utuh4lcIkavwIR;_m;X!h>_eAlA3lvdn;P`*+5nDFyN8dL!lB8enZ>_edY%8?^=Tje<A4A7;pwk_{G%WI#ZM0L!#Dr=!(TM=+C4%;k2(_)lGl~xSy&%e!wB7p<bqbH2m}HC5a=_zQ5NgDIt{wBRgT&^r>r#DRiNrhZ2lmksFNXjEy9ymhc#T3!@hFCc7`boqbN5b?7^AnEF6o@!lBG@WT_&sm)MZWwJQ|W{BgwUYd)424*M8Co*<0X+Ab#E>R4Ad%F@tIDZ=88L45ZzTcQ*}`Aak-BcmURpy*Sqr2vs{cmhXJCcIly_NJT`W%mwccSqTa_cG-y%1OMbEIY;#M$o0~C3=*Sp}^sq)dMFRPKQZ(ZlpW`A-fcika;ChPs%>si{+OH0E}3PLT{c4XD}0hM5eDKve8af%C#zm=all*Qn4kk1ei(L_a4Y|x}x<@EYeai*g2k*4RO>_9m(~lD3g>nCQk&EHE0jPR2oB*u*6UDYdhtzWxrgFMrm;$jZXMU%3&?#T?iJ@q%{&Rknz1dZVid7?1a%3g{I>ZfGQIS@OPHqfh5&c*_(1&ltF1k<$`}*x;H2{2?!}sBHf}>1KO?`{}=SzZEhC=|7-N-EEuO`r2l?_g;&va5)Mr`c8s^qA&eO)F{(fKsZ>Qg1TKYjDL<FCY*CpldK2gX6%#O%p|0tTx16u;wJmysV^Z6g9FX1|NM)_aO0XK*rGl>td&eMHTTkni2tHyrGV$|ezv1uF0se~1{<F(r?F1NSbm>`d6JM'
    'zfKg;FGPCHGCepznw`9G1uI*bss39WZ6CN?2hJ~C2I^WXq(te<-d9dyn>3p?S!n2r5Fl&H)Owshzz0;Ba+$|_(aNLr}uc~Yu)hh79N3hFQ_b*fT@FFJkUu&{7GT6hj9yOpdD??sfQgh>*zIV5Xb1?96pHoO3zLlOx+XIp!4j1rp`mEF2r1g3Nm;1^k7o*6b?y>Fa6%tZh5eE!QepA#KM&umlV+|mm~TR><yCWUTpa13=#BQ6;$&3L62KD%0#NJLTKhZiqB9@x);j<sByqOxDF2>>M}b7uT6C5Qd0c7Lssw3^ObUU8{dYm4ZwC=%sm^;`;L4TYlYC~Ra!{oL)`{>~}nu-EvH1lLLdBxs_{ebs+AbMDK})j6B<HqQTf*q;NjJRCp9etO1G-NqLpiX}Ox#$Q69%06rOJV}2%g@D2oh;3a-!M^k~PibPQRuS6f#I7sF+5-q%kud~E+8_UV$V=w^QCYgj`r`dDUfCaA{i1fnYqhB2@#>mq(=8q%tVI={PwcYHItBsEO1rZ>HG72%8j5ULRB<S!485>NS5UTNp<1_gtCo@H^QdZ}O1{BMS(K?c8L7LNNQJr<B)_5bx3=c0+J)kEE}}Z8h2kjL3o0sbtuopy)Y>BYL8F^TqMHwP5ydJ`-cfHj)oeiFr+owZf;Y&&xeRpla5}yeLPV=Qq`C~W6oqiGALl%6RtSPRv<#6aS&pc0L+bH_h66@`hzr$ER|e4uC{l!D8!ic!+AgoiMt^nX^SM$9nik{>g9r`Nks*DUue2HaU&xlJ$#c$P#yTaMh{E$dtH7^0NbrXorEDNi;1OCzq|fR?<oDIV?kx{?NgeEpI@lF?u=}Bs_65=?tg#-v!g^q4U|>q}VJ-^OC5dq#1b&KC^ZKdm1-~?x?XTWfac$aAr}9>7v(P6Ige+rvW?^rcMTE5~use+m_bNtA8{Z$1HZ=5@K@YV016w}|!_6d^k|&Gjh1l4YWd~B3MJ9oy(jpob1sp;UWpB!9QFiZ8cDKt#v~#PRMLCI+Xc8x5LI0#RLUva$bOci_r$F2QoBPbmy8+i=4*%_X4nxN>@@I<K*l~C*2B*^)YPGY_YUk%@wd+r#R@+ZnZNY;~8t$a6mAq9$WWg;YCNzbu6Ut{`A#s1%+t`$DOSRVK@ZU8p@d-8eC*;C>7Jf1)$jKC%Fb9%xMJmxDqSDxCO9N#?!-9b8YV|L^RE^<iFphFaO@2(~w{0XsGo$z*8J;l5CG-OQtO(x{MpyDIeX9fn%cV#tLy;p!68JEbCX+F5^nA+@iQ2r!8+9P}M7A=xYP!)gavozD5%h{ERY#U+TuNj{O&ksLFjbhKNPD=V?Gf7O{5@Gy9FHF_1@ycy4s{WM98`FA$2_Q%n|N(tS#VRp9G4BLxW6E|OSO4JW(~?5r|_(h0)iqf)@Uq_Fb@A<_FOy{9MDlmNE9MT!;&hqxWiaS1+l06jF+n{U)@iO2HbTtm0=6WkvD<F;iZaji*js9_K$6Rhrlv)2$)OyLF_0=mf7X3Fx_CLmg1C28+r;T;&nig{?)>JDV4K`CYFW2IYnlYW#~mg``Hcv{lZ4%CZ=|>oCEWn%W{`zr@8FwI$D7<<)tNh-0*JSisiY59q$Ce{I4xQ-2*JtOQA6qyxfuDo38|#Mu}BO((OgK_^+-MVR4qVW<n{jCOLb^OroQ{!Xd!K6`(7L&C+VrS5m){<rQBdhm7mzY+qyqB)U?>mE6#K_)5Sl6dS2s8Rmq(sHq{Yc)Ie)LX%Qe93{`^>a3<r(3ZtFugJr)y<#SvHVR7{SBkM6)R6P*D?!3E6mw-^H2>cQ>2ZVdJaozvNu!dTEc>dB_>1FEo<)S+sybd6M+?g$6lZoy1;y;17(0%2B^^4W;q{eQ<SmQujnl8&pd>xAB2u0#PRNOWT=~hq@@NO41dEwfV2V^rzKCBTFnMNAio&}*StpNj8^@otaeNS4$V22UBqDzW<;Vw<<Rvz+jLTuRlRA~14(q2v{E0A@D%f8Xp(}$f8%h&J+(1QLgbkjc7QW2oAmX70h#rYIRppicK;4*SX2vZYjQk$x^gVbdTky$#BQnPp)O_54npXh}@qU>hN*ZF?$^|T5S&r#OM`-|<B8kyIu?J5g4<7z<F)owDOv_SMC6=O)oTbRPeV*nZ&&Eh6LM|ymueIz|C*N%8j6%3t++;dFM{^T?ek74mWC6D%zk!$o#s-3)%F?RW!lKm1<kuQYa~R6>hmWV@#|MO_(Oi%*abML9%-pJ;jbp5>7lk-5*XxyfSk>jicv{reBGUEFmP@Od6t$J9S^}-E0(k{nFM8Lqb-9PE>MZ5wwH@brm3R$dyB=(`+p?%TD>Giym7DsaUL`3KJE^VfeLdKE(R0SuqY<>kta*UCQI|WPlZUCK7!6-F;}NQ!#8H{;D9afXeq`M%s@@jjuQ#O7P8=V)MN3<U-gK(By)3mwH@+a>UuiWIn;T`AYQYAYdYtP;*2CM^Z?z|x_S?GC@2_JO&(qxLx<$sbf8QD)?r+<__Wi0eQnjS!FYEeu)!#e6(H_63C-eSE_fIwbS4{tAJ^vNTn*>j(GYX$lfc-{Whv?G!U|d?AQ}JSrXG0{U6iEV|nHtWl<@HSRQiH@ZUi!mG=>$WkN+1=kN45b>$}P>4q+8Yn?4Pa2tOY8z9<tu*ZQW;cWOMh|{byLuchp_Ij}@BglJh90o^>6A2=g&lo0){H8yK^GAk{1LA>t(9MZ^y=pFFEek~-l>=_Q?50_P2(R65VqdNJ0sieYT)_%|D4dxZTI_*!q6m@C_5HeaagFGSV_8hSp_GfNLG-K<6nqQbR%Q+KRrFHZYclxrJvG!CEA;`i>l<UsuwSa(<IJKn!st1tRHU#l<1+g+)LdH&e>m9Fp;hTn)bu&fCtSG7&l;?HThM%z04cH2+Uo2e~DulCcRkC2+GCS`DIYoawud86%nbUz1G^H*xlj91yN1y%E^=5$TWp*S!{BO!IT7uWn&Z9&1FQM>kpsrEW=1hA~42YueI1$8Els#dpaUe$tG=X%xZHLF*snswS*TtQO^!OW_*<tfWfCA_iof5*PseygoEkE_iKfP|TO)mU!9n77-Sel@!@Mq4Y)eDd1cu6eV&r7J5@)q<+|D>b<iUweJ+uYH1*_)6>2eNnYgXE%O*@=B{(TSMO&BGIviP6xY&%$7wYinyw3Pk_lB@hnHX=6IE5AfK_k07yyVgy)%JWpx7d#2F-67qAJY4k2Ww6JK%q1i`VC%?Z!c-Kzf6asq@A^ID?Eb<Y$&OU79pG2F6VuGJOz(4rosjAKz(4U~r`uYge%=cxdPB@nSZeR&y^K55YoD&mdsWzAep>%(|RPA9(KZtM1pC%&^h@g+t|ov$$dP^i_sJvY~$1irfRW>?Ii`xUQz)z6>Dm7tskirk^2KI>gwxoy?|4nu-HG$U5I>b>@)5zqZpa`B(_Tn;jwduW{6c>XRK3AFJ{Eoj~c$)zn3<bsvReN}pgQodSBixQvModl&CF#RYVCi}Qx;Q^x#<zqQB3ZT{I(eIJ1X5$7<h8qaeYzot?^7HHpMvo|t=t7!cbj^%@s^tjkinP5ECt@x0vnQQ6S-wuzZ(iBP6>Vq~6&Qv*F=lf`M`9o1414mL&SKs~a46bX5xi{duk4x5NcqhnYN3<8c16Fbw?P<+vJ2xY*|gbS36mAFH>$s)p=_-lUP@xK>G^8rM$lTrqD^6}20|fV<mpOrR_|P$)jTh*=v6RN-)J@3T4!7I8lDzf)bR}jI&m=EfVk3D{qHyVS3oO@(9iDI&iihmQ_5eOtmCWN&05fV*Oi*l3T?~z!xfD{-L8363s<xgan@t#GjrV5jTlXd5Q}N4N-~12wub)TvW60BP7_!JRud*sqL4}&Tbzz&YOvVVRa25g%Wq$uis9a?*?wW;YSCsU^VPh06=T|xSf;M8CUKP=#8y{*b+@i&0%TramEcd=Ev`m#$BTK#RRq*uUrkD6A2zQhG-$nX)k|P$d$kw^!RFPX4B^GqY_9g#SYK7@qKG#0>MC-SXJwYjSLNv#`Ov53Rjt1z4)va^dAb@mucqm0xbvzsUvQJiFikc^d?yf~N_K$(!dO0+1eh1|2t{B^%Bzi{{d<<^KXi%yg`x!wmTmodW$<F5zZ0hbLC+Wq!Pcv-ryF$<Zn7IF%cy{v^lKY+9Ka~zYGhIOi+T}tI-X~}mQ_88dQkp@h)l9whX-&SVufthgK#T~8702k_3;2vj{>V=RUarzS?WD%G4&d=wuF*(J8I!Z-J80*Rgb0~Zq&W0yIb{W>S0~?LN1?;3q)2swypOC+1BA7vQ5^h+hj%IYf!B1zDBI9+Hcc_6Svrj(tRLS>DVN2$~Ba(Sl-rlRvD`sO^Y*<2rq5mlhmA50WHcMAI-6ByDnXrpIc8R=*kyS&(bC5`E?C`wyU1yyoqyND!3T)eyV3V$Hn<K8=-iT5-mAji=0>S|F!pS%d+guTG*?=3XZ{8AdMVzO7kZO0x&i{b3TSI__ZX!U>k!^*s&uB-hyjxx#xaA3QyuuJ-VxunO~+<)!p;3R*iq}xk~!7yHzTcl;^zZw2R>ynZ)}Mp%SIQSe@lP{p*|0*1Ht_24WF}=OlM?H$koW;PD3BJB|DPb5FL!jE%4rxX0hqTi#emwyKI<Kr@j<VF2N4Q?%DWLKf9>Y62eR8}c{U3HIqFQCEP5C)}n6ytqXOnsWJ4GP^v>Zm(+MDG-9JrX|9+<e8>VHGQtBlTDv(`gB7<l1VK=uZQF|dPh%IMaF*M9(Jnfb8c^sbRjl+3ht4oV83jVILP=>cIy$#CMp{fsU<;jT0|Ao!sD^mb5b&n;EhvnWs$EkcfJ(Cra{(l<_d21F;1j*iC)>%f2^vHsqk7sM4Cvum?qUldP;N;Y29K1m2A_xbN<bRr&zsn!o{u|Esq~7+`=Kq(28Qj*QJSgJK4^TfBiGs!D)l>x$%-o&xf2ZF`s_?W07_>6~$JBolC}7%J@swmhq^gwi~aycRhf1^V$U3c}F`=#7Fl26T*+;rfU+`Z0R+j-pu8_{97L-o317GGLLsm{noL)qp>NmBI)9DYbN5Zyyew>HFh<pVizbzoo{&RqB2tF3Ep3GHSXpSzQ$j74z#hWQ*cd#$r4Jj(rsY7Oq#LIl8GZA1+l<yX~8ByR1|C2zhl&l?5&|$byJh9n;J_eU-x+|dgiV_%)8u9-F2^`TD=H9uG@CV^XnY8Qo<!{C06R{AVOWj>VA5tsU=ps83~+KxUB8Jy~Wh$myiGZiG@vk*11;t%5kZRl>d9%4Yjuoud6uRwR0ygqV{%|B--(s_QYz3*2RBb74g*T?GtD-2260<A)M{At=f`bO@ddH-Z@Q_#r!*qlzsE!c)$2`%UZT6l!|N<&%v7eeOxdNETPreKHHH+MBH5Dx^^|%EJJP+K7naAW<Cj@Mv;;@u^Ol-TD@|?&D0A^>6f4@9k0&W`&9nj<-H7RvZxP3swiw)WLvzbIm#E4#DgI5AflM~K3Rc$5HNWGdJw(;O9EMna_58DwYh~&wn=0ml5HnTQA2H^$}-z1OHpy!x9pbHYWKN9w{|Lgzvt~7xSpkN$3CCmtsPmCRn@N1POWkokZKoOV<VG+#X&nrc?q<o8pUms(EE^9D9Lul?d3)Mdy9+Kr`wB|lYS9zW`oLlZx-;ny_9j|u1oA0?6Pw6q}0DRo|LJ8BU4nGy-n}9sqYPJx9E3c-pgM7#(Je+DzW`|bu#UHSIr#TGFC<=6`@kry{j0~Sa03@p+c9GS@o8i!$$Ud1MiK@MtC!q&iB?3D|1r5!qlBHPVeP{`oaKo)9-ZIom*aelkBC<A>%qdH@^?v`*G22dL`W!SHBgOCVRu$XdelJg{W`#3Y)5QSloPmk}%Oor{}(*dW+r5QU~E)re>e$6`FXapHDNrqLje3u`Pme@AhEVE$#0!A1%7<Xo<PH)*#!g^2VBTzi^vam*b(^#;I}NQmR~4BAshG_s~A9;-*(4QG-5-Vo|AZD*@BTluqez%j3@vp2V|?1rgbhS+)DCC!t}6RJH`*3ZT^b(ir09>4ZmTc78w%Kn{?k??UD6R@fKDj}-ddiWhHI73Nf_3M_1dx7;8b>%}?LRQVKaPGddC*+kyUB=TG)k;ihYN?O<)$1c~bT6THMu63P5>H{pUbp|?BT9xhPJ^Tlp$B#X0aXb66Y$wk1_s)}Xb(-mCjD+yi&0v!W$FdNfGMlm3<TlDzWyf<j;RV;a8D4*&=dl3~O^q*m5-G-6NY?7gXz|D;avr%#9+-rsQu4gb;dvpC>%FLHCr^8}{kE82AzX_<B-UPD#DBPjGUX+d>HVerNv6vx{O7e@7pKbNEgmN?Tb&1V*p%;O)pD#Y&LMLyI<r<UKt-0$F0!wr!u-RTEKY$-?ph{OlU;)5jhJ{3zS8*t{guV|N}Byj?+0kln8#n4Sc_!{2|S+&vv(4+o)WjMGD|Gi?66kcs#M<m{&`|#){2uYnL4h27q}?>QARv$sj@y@Qe|DMU#XB(&OJ*n%hIvMeWK>AsOX1{s}CLS#QnZ>>5aGMm9;kCmo9TEY^Cvkl%r)Hv<S2!i~aa9Ti*SJjV&@;Y0rN$bNbXR{-h&Y1!9Hp)k89eYPah6iWIAruVl&NGo^2o@5x#qpchNF`f#^3&t(kG&|CWxmo2oex<WrDVy%Ts>Q&<1@5QZf=f^%E#&WiPlP%JVsY|v6vWs8CSzhIvaSLZ@BF%wd@+!8ABHK*`gEEo>X6-;6Z=zUcqHNKEEH|tWi-$?Pm6>ZVvl6ucG45OGwK(%^Z6HA^G>WA+Cs7fEo3;x3O0JS{Ha4y-Q6F0!OgbKRO>mi+fiW`)ICmf0^h-HxQQOpdKA$gxX1BN<kYJiD=4d2hJeX^fi0P=v>kmmMm%QZ5TSMDh^ZC$QL%^m99rhy|6bZ+~EDX3jIV`b+0FfmG2rSjF(Yn1uWxIQRhd~PG!D_inu9|GG9rF;!F%R3a)lzG<gc(x#*z;5?JggO_T2XEwHT1$~S$z;!-YT)`3%9IA9ZMEE*TB5(LbrS|$a|K6aXxEB{l{DLW^!Rst|PwxncMC3)6ueKHgvmMpOLWvHdS8wh?VoptnhbW&Wn93Rn{tfi~0RW5e3OwtRQ+Ste_XK3>H{2R@UM^)vUtB&FYkI<-Kr{j&6fp(`4>$RloJ%ckR(F(xNtJjhbpLZ^kF<Jkft7Qtf)J!7p#EiWoN7D&u2`xYK}>{#&#heTR$yslm|>$)M59S`{7{gl<UqBq3fk!TiX@&}WmQDib=d=&*}!D>)pZ-^#ibYtKv4O_SPvJgz55?T-0tcD!wp%EplLENTQ!?yAh#@I3jvy){WCiYKm1E7p7^ai|t!CZo;gM`^;CWAn+C9K4T}xzjP-!%K8|g(@os*JYEVj|7KZtQ$*b`OEfbRV9nICf?8y(_JTQZIQ^MR@~bn*{Y~D`5$6-eAViTTBU7zyXcVHgV?Nn-Q!Mx|1HYV11*Hmze5S0JR(j{)^+N3N2kRLuUM@--3qEjqE$K>hI+ncHF*;AX-oyQ3Ujl}%;e2Pl+WTo?tL;0b5^jV9w`GAQ*@&7rahw$@FX?wG~wq?v04L#hN<3|)}KVDMb3ViWNTiU=-!%a@oPznk}beDlmru2`q~D)C`Mg6s4d>8hF+kn-Q%X!TOxN)mbIeaDo(3zzqf9Ry}2`WO2)pb!^f%7?H|AIHZ>J`$<_UWLlb30Gy57I@hM2r2NPE{*3?H}l+eer<u3AhEk{td>Df}3b<7+wGgv~c(1avD-zuQhf|m6g(*roqoqBuCy6V#Pw9Y^*KsK2Q-pl2!`6A{2E58<{5n9IP21Dq`eJ+Q}ay=B59ip(H|IB=YGs|idR8FM9e=_?(X2m9WtL$y%sg|(jDK@IHj4Z7s8I0JsYU)qjl33k~K5=ysDT2E9^oZW-v5f8^&3bZ25+=ohX~;b81@k5NwLkLy4#lOkYk0Z*=clFf&%SrQE?qxIdU?NyZ|^Tw>@pIj%{IFgWwrlZ-~UadyL{X7TQB0bUi11}x1@#aw}SEgxqCzMx<|FnI&l5B^MFg88|y7~=*qx#B(VcS;S=~LmkGS(=8tQQ>NPo){&!8$sQ+C9z~R3eKM4Nq)wSjm|Ka|Y8UD}z_TR5-<b8JEFFq8#-3fD34{TM0^uN^SLb;u1rPFF>F{P;r(-SqZTvXxXA9jv^US{~RieF!sSMdGcp8|7#+wtFTcptx8?&IPyPieUc%Iivr9XsW(l>Xl}PvWMU63J=~{5^g=%f0`3aqpjAzuS9<Z*4ZlP&(JH{@u;ayGweP-?nhJ%j36sna@AIczxe?_RqJfD?u%BQkv>cxm%>&C*9Ow<tBNrqC<{1ets3PZ|rp4gznaj{sZq5'
    '+<rVL=C&QTEEB5^u3o1xwjg@8z@@dP$eyHnHlb?m38E*e9;&h@6|-l(i(dVHoi)Y=Eo^*cYKm(FRwulC1YK>Jye>1Ja#wWW@^r3&xhn&kFM$(<I(K}k-GfWlc(Cokg=<Xc_Ta9MynAqKPwjhR>mS_pk#Ey`v!{!mq<SvyU6lnGg<;P}5L(~!5rF3RtXWIa8lu6M-*q9!PMBZ4Y_@w(g)jBn>bgF-u4kM1E#zT+t*FXZ&wM?Vm-_meFZ;kBTgA*J1S`IzTearCtmTthwkayv4hrc*wps)4TVE-$bglP&^Sza}vcB*C+mt~|E3#JD{Fs+k%6)5_x4G8Br?XaJt;#;v+*Wg2B_IuVatw5yhR6LNH-8EzOgT8FRByp;CDtO=icTx+ZY{gu^1n5q)Ygh0PdctjIo`^bk>&1brq(~r-hYr;Axwo`)b_fkzj3$LMe_J}|8aTuZxNX97pp_OP$xL)Q%NWm3#)6&^3ql2_Pz<fTW+x0sSmcIww=(wD(og)1U-fK0rhv9@rDB}9*z5q)?FieK&D+apRRux@D@wGJt49Tvcz)5ZYzWbP4Iw<50~#Q`=3fCneEpx%h4@w${+rR<wXfM3r5&%=WSQy$h_b0*wZ)MN?`Ohgl)U(%DfTFiJ)7#vjVnWQM6XWa9T<Gi;=PgSwT~JQG1Jw*X&}spXOTX{f<sc83gTC>NllZizNz*EKLxxxYxwP)q937GG>oN)nwGd-s_po1xp*=*R+NfWx|=rK?@so*R+#=4wP->d}{B77kUXVu>Y<yTwUb^&hD0}uZb0Z-Qa6xN0p9^ijIyde9ciU&+|_$3YoWSwCelC=W80#`0>fSJ(`rE3Yw&r`lg89)E&KQ`)WO`ox-Pxe|v>;1OKkJglGI4`b0eazg*2N#~gdVu-j=DghsrdnZRnzbTb)SFFbbh|M73UJheZKo?6~qz^=6V3&F3dp<VYYbT8W!5SW7g(e9kx`~D5yy6Bf$b(UJUK0~X{awb;WN$TyYd}3jZ4F99cQ@f={e5EU+ep7qq&1Z1Sy*%@8Uyddzh2$+!>-O)O%GY{0>gg**W$!km|BZQ8(R#}Rw~7xpXRxiHi}f#cX^C$pwE8j6e-V|U=4DtacTd>@D|l*}9IsPYKfe7ojkhVgh?3hfdF7T(d{vdt5p|9QRmwrs%cPsb*>+X<RpM8fyT&D!eYXhCzZ=rV0Z(3qyS46|>qs4+U8DfG@sazlVy_7)>epyXZS*G=<@(Lz>2v4tL^_MA%*-QrXCa3NUeUO)Z*06BSzyYzP5awLwTbcR6|`AcSMOFGKN8LG9D*Wsg0AEs>Ntp8mLI}k>+^3CV~|-gAf5wb4Pjx<Sh;iXzGW}CsW`s0zApAPZB8eZ-ST0ss*P((m~wlC=_4gfzO^qaV9jK89V@Z?+KYSGwmPW~=BvG0wQKj~H~P@g7Fe2{#sWs8NU+rvtzt<+5-*~-ePNfuzDuAMfi%G-kHqDYO5A@o^BU4^`^MO(J5kc#@}B;gB^CbVJ*Bso_X~Racu)H<jPL3?0qJY@`g^{wNdx#F{-@Pf;`QPy@%rgGzB`Yx*Z+ledA;Ukd0o7J?tFw_?e7N}=THCBAH4kZ%Rl?q|MFk_<A3w%(@($q|9<+%@3a2p!Yt?4m-mbOsSgjMrmbO0Q7^mYCvXm$KA=zL%R`!ye#29zzW$<w`=iM4BsFI82jufA!u&u@n}GUZ^(hJZ$>_|FRrg07a=v|iRSVASPg?V3_2*%K-q{b7vZO2Lh}u{}iAy5*O%+i3R{gQze!SFG9VWd<Gk!Bvg1Uwaa#cM}>QfJjDCDZ|>-y|ve-vS~?0HnxANvfX%ELaZ{)YQEK~b&;+@Fm8?WI!d4fWH`{`BPjcC5cS{cTTw7V8{j7R!9&H#Fs9-FEHYLp}S}U+n(e_it%CQtn@%*#Gp_U#I%}z%rZ@FbA9+u<I{@oi_<_?N!v?>xv^qWWZ2|aFljS=IH=@Mmjh5RZ?HLu-`8}%z@r{{Fk5O>+4GlpI_oDX9|kL1{H@xDh~5h9KH%;Af<}fg^LXVEH)F1&BoeS#*%}Pg9Q&u4o2<JoQ2?F$-&6MVmtI~6$5u--vJhZ2I_`2SR<)tEi%BODF+mh*ok9$sje7lA!5anmQ+>@@M<^g7w~>3a8_0aYe%ts5YrVe$-+voi}A4Nu!`4&g$1L!=@3gZSk@SQWh~BM<=bQ7#ExV62f@PQvHCzP+I!F4SU!k_ofzSLzQ>A#WyJS*Sc3J=daOcSp2$1|@^WO!pH=PU%o1$G2C^wJ<8aYfR<#nN%8OkQH!Q!BsaT|{kvcK6=^_F(7#d0v^-Og>B!U{!)R6ml2%Be0&{aZ)>h!YIz`FRZWO{kO;EG)+b46EuTZRfPtkH$DMNpTOdS<L}S8vk(^i{oGLf-DaAj?;Sga==SirP+%6vUelWzNtnRIyPgHmbD4Cb_p|X}1;nWUPHI!XuRA#!>V;Oibe<y(T0toNa+S-rY-g_ogTHw*9^JJLqlC>diZP%Y;Oj;BEN54fk#bf@ZO=D_E-)Zk2b0XM2%ey<scGF3mJtIdpq}#kQAuAwDfurMcb=PcC2vvwExEk%44~Qsao(H>_?Ao|@QlNAO&T(3oc!N(dgq0h$%TqHx~)fL^a4-0YWA_Lqyg^m5F8XiMLuwiKS`T62{xz(7oXpczPP1`-X+muchDZwGiF*;1fB6$v(y+U`-SS9@&HV_!EtZ>HT4ZgGPZ?L9eb*FKR)Bh4(m(<ZFDGItzC$V8fjkcnJ(JiU4e7`^(XiPq@4eabZ&wGxmC)ETVaW+4$IZ&ZkQK4c;ZB>I<DWL-eQM}W444j}0O()J^9h~ymzJrqgb9BC(V7gD|%l7>iqGQw?7JCSU?a}H8Wq+0s{aDZdHJdTKLW~`)=5U5$Us@N=R6h^AyT%vuWE4OU-2J*zdu4naxS+8p)<A*xO7jdsenYy*xiLeh=Rr{i2-etYwt%H;pLz|k&5HGsu(?y!8i_Y-#O=tL->kOmqaZoY)SujU5b}oQ2Am;i%97JU7NAH}*b<9N;$RXCt9z~WxB~W=C`9fi#=~4-vpxV3*dX>^q_LA(ac5i|z{{)Q$ZN4|o_Gb7}XShA==`C>Ud1UXibcWxre({@X64S#piQOQO@AoCT4(JRk)EU;hb%t3h7824KChMT9ck2xEZ%b!bo}x3XP!TZJ8MgORHoe|dhF`)<yrkHiaET=R!-i8_#J6gB5E|3SAH`Uak(m3dbURlToXFYBq8vYw?KvweR}@SuPlm5uNs}<%f&Qq?=t}h(<>AgBRA(~={n5%trZ~der{zmy>7p!s;A}tb>`zbbZ{Mar?(8Sr9}SgT!u@g9D=%a6W;yXawm(jL9U7{~YA7qKp{uOEBw^40?&o;+pZ#b5*?;!mc@CP!S<C)v@uM?gkURSqPW+#2!Ox#wzI=8}_ePw16vtI&&S}sT=O3$tHJZWDbkbM@x<(>w*0<}7kZ`!XG3~i=yWYx!uc}6_`K`CevMAM;OtrT4XA=E4^(KqXuATZQb<uUDv%66@oYGtBI;s+2teozr>Hd7Ezf%|`;3oc?=_l2nrF45&zmDz=Zoi5Wu1cDM#lwP~RT^2)HxqhRT79uA-ui`;^ePKS=*?V(4to<%liYL-?`A9V+|bB7&MsD*9{!d~FlvJSHx-*L%(%~tcWKy9Mt?H;TeIU1tL1TJ22Iv5={Q8j!A6EBN1Bv3?Qk!vzZm_^>Murr^$ssGY=Nl182#0-9a{a(vM5?6&Fu7BH(<uYTQf&Sf3W(a(XYR$80?ArJyDo~8&6ghL|iW^1>JUfXSLb!nwHY<NP9R&sHhCOpE_nm_A4XdpuY_Io8Dejf9lT^?&npt!gJ00jBLUxs-aUuMrorEi>F9!W|Hqh_18|c6gSD(m|`=|ooF0KPJB73-i4w6rx$nJ&o4i}-u!X1)UG?(3&_r1Kz8;5Y9>a_#8NXc!zJ0ae(5*Q@>SiHO`v^c%*$TjWnefn8=TlT!BnMC!Si5@AX5+IMUF+wL|TCPyTg>uMQ2OUEMfug2FRA6v8ay&kV!#f$+jc7n8VKgGR5jX2~+m*l1vQ5Cc%sdC}P>e(m{+)?8Hv&#7^wl7?k#_U``pwnUyw<Cn#chp`-2H_#kW%y8hWx@9ERcpJ^$5y-HlMnI#NKGdkSKrv~6-BcxqICvh3Kpl{m~Tk|6$<O>34A^?`J;MonzlRA9kzr;&Iajm9N9gDP19W8?heH>M-rf4}74_d-?)6xiLrO=JWI}9pJQ8VvBM!KD?v-PWQMf|Q*r5NIx`{~wliv7>aDYhg%y&hw4FY)v1T8Ko%p%kffmfoq_{zHZdF&O4Z9{mbi5$f!p*P0)hbX;ZkPT+Via0Z1*AWB#6`pu6qt{mc;BBk*M_e6lV0lv1(vk~Oc;&$qp7WadXmLZHQF*IKq4L22SP!KKds~OMM**aTywCcgu{27p)R<K)DIbB&TN9L)}>PNuKhHb3X5jNT8%zewbZJHfF)o>~ysqW{6v6+>Z^Ag39%Safvc}ZPn9V+IT6h1qr*TVMv^NYpw(`GS^VTZ-^%=i9u?9BImT19{J7*>|thjF7RHi+SICS-~17NvE65nFGS+AAp^t!m9#RI(^jC1wjtMsEF&pDPwduq0Q}U#Xr$wlJZL6jsV=Vn!*Y0`!~0`fg&){?6!N$^l4N<}FM)flBK;#*%|+_fct?hZyiUN`}86!m5L{qgXzOp|uMJs=Nz440&?U43^F3;A6#nws<e_Fntqq7&Y4)MGtfi3vI$vr8*uiZ6`*yhl}PrfVYi{RojEd#n9Q246l+A=6Q}xd6jrIIQG`r5HIL-osEPY%nRTS4gYA};w&!PA0pd=lG!THz!stFUo5)jw^io)^w|};lGxJ<7NnAP>n=b%YVbi9N0Yv*#l;mNpzxNJnyY9*gSS$%7f5uLi@^Y%t+REu&epH1#m;v!d={!KBtP9+j<Nq`(H(wx{$zStuHOIi(~RDbt9Z7Om%U0zCl##H>jg#FHI{g|XHu%v9aZ6d12UoCKFE~k$>7qfFl$*1ZROmMWVd=pFnpM1t~aav@D!=Z`wV0(OQn#RdOxzBeUUERxL9ga)n6>SB<MPjg`X-xaclM~@r$B^4%xh-kJO%8e^MK4{bi}fb?MS19l?jMdFhB2T?tkuZBWttE7B3-<W9Pi?xZ{EPP&usr2DndG36`Mvvbb4=LeaWH0O8|7DgB++oUz!;AB}nlgH3464C#9@uo;OiRk@mRw9a>5Ld9|L&|_7>xw}MhYVv&g%<Rr9)!%tSf!?wODsuX-S^0>$Gv1ijx>_yBo$BUkdlT@c8jGDDN&?ZDZ-N+f+H<>5<*t~88U)5LX9er5<JNuJOfK7c48-XVkh=w4A%|PoR-a96=5Oehb)=g(H?B!mj1UT{pPLQ%okB^#>&DraFZ;SGvkzVBw^<iD_`D~BO~kx5|ld**U<7{O_mU||C+2)KS|B8a-5FR4~+L$<>Q7-`YNbL^Y5w%9^lgY{wn*Ef8D(P=J!i^B<|@ic0bMZcl@x`pPt#@?EZH4Kd!&p{ZD<q#qK904O#u!?vFG5-Fp|?{CirxesEokJt50Lxdfz3>CPL~*m%gkI%JZxoa#`0v=3(-u)pmsVxLzv$YkDR=@hS15ng{FN<{&#o8tr?q&7M?jdRvYYKlGk3y($lms>IIi}qxxr5$_qN%c+0T6YqAPA3D!iM~m+Z8KA_Vb!hLj+?XsqlnqEv=>!yBAr@8q{HeIVM146m>G+Q7}|_#TS0BRXAq|71aF83ac8SiC39S;$_p&PSuDZW-!u}D-LwYjDH$O<{TL(-k@g)TbRrW-{f?3Hm5^+%sv}6)kJJN5*@GbEc9p!vP6Pz+GVu-}w!#-61hw^y|4<rZCcv_-6LCU-=jqQ%RLQM3wqzZZDNbOkWR{bo*sRK>5F<}9=XGL#I%gEYSk2hR6FHGz6Jo~tM)bBxIiy-2G2W{^$RcF??-wECQhqbP3mETLvixTMG4PJx4gv6kSBFw`UzMi_==tm~4HmaE%&!1ZQU*_#kU`jXQXF~_Vva(hHY^tYGghwJY#JPaDKeS{MKX~D`0Jp~&`Bhk2&-K>iKGKa+mA$`sXdO+Ly`0yBke>ckn+utbO%x&f)I3ZxEsmV+sGZLeI!6tNl;;$7%7$=k;N?9{wTKli|za}K!T0*VFMiLU55<cqb{649kT&z?RxE;Jb{a<7_99C+G|Q_RF$2Sa}+h8%ES>pQ^-u6$cg+WkQsp^ObQ&PspJsC{}%D%U%iVTnXb~u`^Edez0U*s7&X|r?xlKf2+DAwg6jC$Af<w+eGwTq-y7Y4!(p$Y(wZI~G~O}7EGK0{y%F{j@>_v5P+EXikO(ax)Ec;pgbWhRa-~5>e}mQq!%+wFW{p_{g;k|OA8q#?I(yIFv-j*ZdLvY(C3NIPc&=h~`rW<DdHS#4&(m}ZL4UvKeF#A;1vv7-c*!4u=Pj5z_kn&+ZdmuxRdQ7hk6cVykKxR}uFLR7pf52wNc9DFs5pJ8w`Vzh)Vm^O7S%#rk64s(DKIytTbiRHEp(#qcJoDAs8wG@%eEkQmje1=1>FkzU`enF`WjN{7SLCbkd1`sY+A0y>_tT~zWKv6{$UivQp`JsWkD0@i)}Ff)no6YZv{lJKT2$Ok;=2SfyhNt*VW2(%BkqRC{^Y1)fpJ5^K#+iE}>5h-1imfa@-d;U7rz&8AE-Xe`I}GM4HLI+dJJqzMIv&@5_CZTfdn_rv0g+kFTK2zi#s{OF|!1L|s;7EkdUaAsG*fp0I#x<R4tluK!~>yDsi-F~pbj`6UKoS-_C{dj_Il2C{Mn5@QCEa|SYV1_E{lqICwoe#o+i>X~P7E@vQBBc3AzjsqpO%svm3Kp!w1(u~U+(u873upRBI;QK0;E1^`0`cNuQ=re)((ENeamzaM{XW!X(_8saglYMov@5V^$6OEdbhoYg*n(Ql+yelvV70{RG81v#tY>+QR4kXEA6|<Ho>*zGY)eibIdEpZNPvsS#KW|(@<fCDXX_e<KJ|eQn2-ogK5<arBV7HBYtyNkt2_9IcGj-F;9m+2!av~>kB0o0Ljv(1YWC}~izvHpUPHz##MpV<PRvPrV>3u>(l4+KtlCu&rmaA`Z|I0qQo`=&#EFcO;QW1iO?3P6`ih^g1YBWIJCc&!2UYnz$<7*K5AgN@SDap8SHUHNV`~T(TXL{#q;>8X3{XajMTEub$NtVVnN1*ee2D7Ywd|x$m0|_R#?^NVALdeEoBihq=fJA8twvjeQNGWFX5J{pwvxgLkMD3W2+^rcB#z<3abDBqr!S>S(66I@~4<MG=s!bt+d9DT$O$jIJ>=y`O3Lk<<QHo2xt!BeQm!Lpg#pDQeJw%$A0)FxtNamBnZZ-1V(nh*lC8!5Q$aX_El3KuyNe%+?Y>$v^B43m=dqaNNfusfv&Mrcx1D1`%F;Y!0G#jzY?d?IxxX~FzAGz@W6095bkTgIF_GNPsU<L^?$HBr={NIbF<n8rRS7l);-aaX&qN=aG&E-+5q)e?DsGgF#4j>6pl8ub4ky6c-;p&s0$xsW3k4r%nrR($_D)OkJvV@~09=RrKL>2c@fqF!n5p+N$ZHQ=+Evh!40%aV!)6cN+3#x?0rMswvfR#CufzvJAN7aB&4zTNM?~Z6v@mvcQ6=ABt<!DY-FjbArO>-|5OH3uGGNvm1SI<!;Ohq;oOLUcaRkm;+70a=t&#U_J;hw4@E@lT+*JLLc?~a`}GNQ_gs+d$;GeQH-wR?_gZIV?1vZpGXig@=N75P+^Q&rA{if)4{^6t2~VIQZGUQnsx*no<fimL3OG9neyKB~Nf$|$Z(22~E0KxF!X-bsbI(dv4sK9VXZ1q9?^4^a`ON?P%R?ST8KBBml}@|>f}K2^X}5gJrSRLPOX=BSEAwFn6R&!TipFF(ht(lILepac}L_ZWn*fWcMI-QW#hM3n=!(~B97O{9(DndvXVMgcOiROMU7k*HS1b{Eyyp!(vLGB`G4wGm_oZYE%~_lf~<6%ebg$%fG2q4p6^1do*>l|$Y9khM*V0rZHug=TB3YrmMPnPw_rJT=R_GKEaV$RTA)vVI48odxf#L(1em`kX^U$n!&p2Zj(Qo{;@i?Ui7!9)(on5m9G&k&4P}JfgmshE$>&kBHc2%YUXAk0`OCB3b&&qQOOFm}3KgLy$%x<(8`l7fsVoGz~l?a)b4Ti(;%F?J<@40AO|(<NZoHomZ8IM^GMJ8N1p>P-uLeExgMl8Dw+&5LrHCC_y#11@A%@p5othhRksB;Eu0BSTg(Ahk677K_)kL2Us$r<TpwX20rNJTn(v$U?J{qoq?@C38y|AY076EA(nHt$_|mGB~'
    '#sy)+QG5Lg^bK6@sD=P~ANb5zUTS2+)d^0fO{eb%+#`g_}Y6unBq5XJO+M!-k2qe6}w@wy#PXXW*_D7DI@2EFa#B7OO}mt4J_d;p2qL1|K4fbvBX=g_Vbp&_E$1qS%#AhlCKaa=O(WNWzMnesDIT_@_956qDuJf!O@u1g9A0k!T{pWFZ|SSv;|WkY#&xkT^nuX<`hPA+hd5$VXsZw&)`{Si|0nq-Ob3*$5f8(+AQ4#412{1WCs2_((8+$3zBc-{I`oh<!Wu6ezvbs=(3Ov7476c$OJI(T8qeal%F75zZ5~yl;!)6Vh>>-}B;d&nqU9%{_0Ie?l}jDU^J`d!-gp;{RQ81AP>aOfMh*_Y+S++I<In!|*R!8*DMRT_JA7uh$z;Z)F=E@!q11*rbAm3VU0*dzz6H8(M_H5VqdLd%?i8WX`!^*c(O2OK^I*w}l*7@p=n%Qa}TXa9|M*!RW1?`%^M>MBvrMy94gUHA-;rjv+j2V0X{Wo`KylH&mQnDc=^f*$c-Lw!<m+A=FD;tybhw%#~JXU?S6IaC#&6TB%Tdf_u5%Obwx!y=n+D-x}!MwyKPV;Pk2?u)TVF_u;@A96}2)_#>bY`3jGr`+JMo3;&iA`7bRVg+v#R!WcilM9MEQCYCN-+b2ztVL(H+%yWb$do<}mG^1JENmGYYI7id&q@g`Dc{qi0H03^;*2WVwK@)e;w7Y1?wn6TqNfYn$qi9+iPtXKS)WJ!JCXH!o8ch)O^~6k?GNehj+H%eW&C%rHDr4T()z%pdCNc6TyE|yACqZwg{XUvv>L>=2m^e+f)i6Gd%wuZPqybGB(L_m;O&WI+NxBUelP3B!Ww_rZ-@R{|M%lKSO_O%fWMc~5Ndz>-)S<-((Kr*7v=wcJrrDahw2LO2H0C5mlm{|9d%Q70Gc+)4y6&gJbswKY14)#Cnn&8nh-r%PD9n{;&{SJ%e4Hj>+hVh|&HHGwshg%<G{u-^V-jO)Lq1W^zzL!$8pDseS<{Rs(R8lUG2HGXn*P%|dfS`Cc!UN_P_z@;S8JNlB$DNuJV}#{M}a0WS^mb2WrMVL$L%Jnxzlv&mSS#L1(o;JxvP*Lirl8ZCe5Od_{)nz;`Q?-XXK)fc)wi!`%@Tgwry}cv;l!#GT1rBno;o#o^<Kh5cA**3Y4LfcZ&sYCW(iZsR1P6$07$HGpqSH^6GOU1A`q!au5ee8+PIGQFu9qhZA?__g;MZ`Gx!NdJrf7{nBCdc3vG95B~dU>@Qs@6MuiObbvYn3GPqXzyaTy21iI5$QNlK5~P7NaNzr$L*BW6V~Bgs5A5>__xC*5zenqH`2OUB`-98{khJ5si$@T%#C}jYx9-Ff9`A14@&u+yygdnzvv@x7XW%r8Kk50WNxTl;pAlXL@9zlD{{CR$X|O*ue}9PsJo)=uZ2tbJ8T^C|#bqD@WnVsNlM)mSKHmI~r-1-B63>nZU&2`aS1z(?xX7ljA7L=@^^>rbvp?4&OfH&yYjSbzwq{DBj8qxDCIINAJ%wx7qmHe<KG)Z-`l?`TjR)zXNOLgyqy6Yrj4s<elyEL*n|(2_f|Ajg*00W{lLC4t`J98QEZtAp!TV9aZv~@R0VDQR!CMR0!T`~PA9uB#DB>K7ohxJkBIR}Fph;xnRti+dbInI1EF3TNus&+}cO)0(xl#6^(M1D4boQaC1SgJ}vKwL??nCJZMAM0WU9|l;C{3dIyF`oYX!Ja^?)NpDMAbH0y+`PyR6V1As@_Bkw1EBDnyfg129pac&U7S8l<Ceg>xN~*0crou_Vd?h<*PB<PdF)Qw;>b`tEt!r7TK<f9AgyhS=7gKBfC$v--m>RtiGq38&6a`ujHVs`MQu{JIjj8Ri2nKu94ZoB4TTIDP6Pc+>+;I99WUkg7@x<N`6@+*#F|<?!8%8$+WKeQXr%m`^>Z<NgRpkmL8$(bl(|&$#}5+Gsn4Snh3;dmc%J*H<$(c$WvWd=_MouA^#5*{h+)*RMdo}Vlh&%XbKuq=z*v?vQ<G=eu`kL&hl{zvec6@d7aMKcZ8x@6k!KNK2Bk2J0D9S*ZY$x+Hs1wgChU%6lQwRlj5X!I7R->DfYZk;YXpU$0>H~xa9#9`8Y+IrwGR>hNt=tiZOSQA3zaCTu!}%B2Dvjc}NjPoMR0m?z0Rj@{q?3BR;tfx$$CBq>)sBj2oOHjii$}l5nt^yp8;F!%(0bxiyU=KjKhSONWM;M<Qb$NWfBxUS#mUda)wM&59h~<?!HGk)s=*{C;mf9{u=cCt=X-rhF^*IPST)7Wy$>AA`pMZh9!xFzJJE%n8BS!>)tA0}mrSxx4HbrvV=C#DjZId<^g|oCbKj6A#`=_%Xoya2nuoh&LAxHcr=Y6!UZ}GdK<KX!0v<3J(^3OZJ$8kB5V}nHX{sPj}+&xp=%2cLKO(aFA)v*ZH2f(np6UKA*eS$KC5UJsH3E{l0g98R20TkM91vRXw)wRF2{6_ZIK`+3xcoPPTN<pYuVy`FI@T?)ggtJl%<VS_kG}cMPWip2m3b`70NXcj7d_lc!Iaz?+Z9L-;-)>*mWh+GhdcaUg)D0p6aB4+Yd?0&X1OPTt*sck!J9{>1_EL$~l>F1m%d=@#BEm;c(j1?QJN_w?jt&Z^E#RA&~e{V^lq-M0Fkfkkh%Tkk@4R(f`p=?*OGodfHnJ*+qy^Wx|lj$pyVl6rmTFmkYX5L+FvjD7qNMh+GoEI2+PE|wgO4r0=YFDvIj&D#|lyXplTjEc>#QXcWT9-q7m%X7T_4lF$ZYsawYW8nx!$FO90MR^`mcVhJk*h9w&Wb}v3_2Fk5+vC^ZQ{IQ8?`CwdV|z$Ailu`XIhdylII$D^j<96AK9eolMcbcOa^;@&_Yv44kNsB{f9p*iqd1Bfrh%+CmIkfT8Au=INNQ#l-BohRh8%bOGvsD+o)FS96z3-_iZ-H1BMm_u>JXCh{Wg|jM~%ayd)*~=sqbe722t~XU-Toq4aQmdcRD{Jjm`ljQa3zF0@jNKSV}xKl-@>!;(#Mtgz|tg%h{wL<1N<|a+Y<licJC66oG7W)l@Z&DR9(s00|$8siqlI7&|!WkfPlbQF~_SJhqY|?50Rc{i(O4X$teuibINEM^>y9V!}Li+E<{UABG~G6hAsedmIHRuI&*Nw3|YwR#6mDvX^AX9jOw|*_Z$t`gD&e;tq=PL<*cd_~8_Kkv)TgY=`V=inxQKSX=!L3adoAez$FkW>L_PB3gdmc1*KA*v1sennMuZY*9p|HX6C8!}8*6sDOfuSEvH%#yse;e>u#?SuF}aBQVsS^~GlRpRQjVkvzt}7*eqCaZC~0F(2}Q)YzIY-J(M)jg8l7AVUYQYP9?s##1j^i@&yLE#A@^CH{U1qr|hmpNe%NPo|=wH-I+Ff+wc^(7_Q~o%wBT9Jd0w)syO^I;l>olj@{;GS!jzrITtzb*`_I>ZCfUPO6jYq;h;Xq7t`}H-{44kzYqrY7~%9FKSPKudbh1bSnS#Prv&|pTFExD(_d8M&(!!m>)2&;CakwEY6;@=j=Iq&YrX9H{7F6Pj$lTQ#d{5d|x<-|K^>8$n?%Xe6SGt?VW|lS69*m{T=V`HEO>^Y`-Gx2%Dgx>g+vx&)&25>^*x`x{62jhI@PKj^47PH}B{T^Sy3>fzeB>iq)1$qIa3t&i$_beD4Xd_4d`pvhp!WOb65VuG$o?JyHc5(nl*IX6^c8(1?R8z2oBQ(9s4KlxRbb8?*ihdN$Z6h|ua#CFZ(smYoax_}^ZfdgA8P^T~GV0WNW0pUMd3l4YfhV6bREbTzdhcxuh-r}LP~N{uR${gg2kS#f4YVjqu6*SrH%WGzL>%7-zPT^S_X^I#@V$YZKBNJM7*prORhW2%JWOca$@MI}4K!f843n5ucDJ+t$JFo|;>Qzhhc4_@p#row4-Bo+KYkaD?>sf@fmf{JjQqoBgW(qZs*Ol74TQm%{>-v!-E14{fnq#}6O1dzsIIIFSEP?71o+EXRNhn7>d8LHUuG0UmQcDn7T+6<K!Uo~_!zLP3XQI#pG`ar5SN0slS%H-T6q^c9o(ckZ#o5WPkIh3ZToSVc{b^LbtRL)HrRC)Mr52);$G^pxmXBtu2H)&Dj!H(&P0@9{DM^y*=JsQ3~J9bfJ_q2k;KSE{Qr0p+oFO_wZng>9`KSX8Rq~>7I@DEWLHwpMJFnou~E_-3zB;X6d@I9*RaiTL+@FqQ~>hjSORPZKUsu{zTONDOIrK(}<M6!OF?|cG%bBf`v1Dtx=ewUbsQ!P4`|L&4*^KI3sykCB#+w>Wc=b_PO-^k_1yp%hR*5gD^^h8heL{IcYe>>=#Zwtw;4dggV&9{ggN1KO6yOd?<a#<ZflZ&<iT4pRPhGpe2nq0Jb<u2kKD7k1FqMoJ3LE{}LHLtiuYNLXm2hnH+Qw%)(23~=-j5iYG1ZtLo$o7yPfd*@TGeJ}(NqjiC9}ez^Jv6yxD`LG__W%1u3eB5k|NZjAvY(s@ASF~MM|ONB^++#JZR)JMZ0h1Vg$Sg=d$Fjocy0*h1y9tNIvNjiA2mIgx?t)$rcMv0u7|1HL#V5-XPu#b|H<?S>V!{ElqZoa>iQ6B0uM9w-4oQsppFNrdqr%11a%1qsr#_V@EGcZn1LPC3$wb9IvUjaVJ1eMht%Z()VzP=iSmP}!$ImT0abVubvj6$H!0;2)LA<{&Qh1{2LpV$cT-2@dzh!F>%*zVLW#nZVN$ml>NH8+0QFToouJMW)N}`R64ioi>H?^%ppJ+-%~4B}v`t+H)Ip9hvXt--q;50R{i7#YnD0(%VqPVCsFMuozmvLun2MSmqmo(+6*JUiQuhy2#|=8vaSwHyq26wZbT-+CQUBhfu3GLX-;^52Jt)KOA!;BYK9f2+)JbiU5wdd6r`C+yx1x6PB=4jy4t1EI4pY?S7`2L7+D9E8M@_a*&DWq#I))@aks4_LHis+;+A1OBXaki~o39MtBP!I&X;)_US*5;}&ze!wh??+re2jY0dHxTV!b)M)dA?s>be@D&p4|@^^@mJ~iWd8rg0NR}l26ufN7Jr*!b(yc4JX_BEj3oe!BGYU)>K*)`2iGVNKp-n-w!FifSWNXGN#CTD2hR$&rV4}J1Ck#0rIK~im->G7!-&R;1sljq8SwWW+X+}Ls1M0bu)^Bc2G2fBI>h2P=q}c#h{QkqbX<yMKdVm&1j0ShoTr1N$OD!P>|HFC<<{ihbY9&APPRzV-);m5JeQutVbyL%|MF86&Hsnh^sRI1sm!?3U)J?q95u}ivDIWML*ObMZpwdOp$uM!hoU~6tsup3#RC9<`+y6_E0o~A`L0%0Tgja5gtL2h7|Mwia4YQkDy3H3VHxV98!cwP^2LRJ%A!UfFg`3(gP@HND&`E5ylkh0TeW(h(NRAQh@TTp*bQu5Vc`inK1<oDdH}QMF#&LFEaS24;ehaESK>$sN%*(u!&kUc|_3sn#6YCis$nKoshuq2!%);eT9*k<ua#aeaZG5lkp`zzX^kU`UmZ$3M%&8#|BgoU^O-CbySKdG!U$u%3!)I4WG=511jPsLuDIG{Tuf01S%Y*d#v_Gnf6nV5o1?0h2VONUbAD0Vm$_{hG90(7Kfr4bG(Zp8&6W?0&^(}oZ<r%D0>(`(jP(5Jc@?T_uUjQ9Yx$hksm`r-vdQ?3<WN4ds6%cD6&<Ucpn9Q4;0}s6mbVdHiVah6cO*Ih@w1-B6*(E`2iGs58p*WLfeaccV{VzC1P3>Aitv24{C}qOF=mJ2l*!`ol+T6D5aZiCQcTGEiXrHx5DuV#dy{MWs8(IlT4;2n_?)zD2if><q=30{7DgzP6$MH6ex%lArBcpgVTr+bM*saR6l7}jxmB!QKsC9g;N@R#f0!`r}Wt&L{A9f*RjY!F1mofzUTs8ulD#4JpjxuD((SBY84k91g@ckFyObz{jd?AR{eqHeZz)1wIHjE;|tXj<!$-H9F?rAAzk5!SihNElp1({HChoG??40as+mR;p4q3P<Z>J*`fxOVqo@Dq6?@N{;=iG34)r&R{d<nTU%7jozfZb*tg}Dw*!k}`?6QaY#cJI{HhXBX8JL+&(kFVNCwihk8cLp!6<r}Mc|sn!hC|<I_%w8p+5X1Ge*1Z~-@d)R#801;{WdvLWw338)+ChCw|GP&X<CVHb@WTtYDjHp@Qs`Em-$7c)T35TZN`||Ut^2u38?Fe{Zn(rM%>CYwq;fsRwJ6mXsG4DaEfW44Z6%tvKg7|&?p5S*&0pTP77$FsgZPPnxzcXQ7+Z-^obKR;1M=MuL$elIJ258-HJ!!XsneYCEGOdUYcsEl&5H<Ofy51_Rv_?%}JV}UFfUPlrXjreU~%?t5>yY(n)jD7<&0#G-Z}1{#Z15mL}|?DLZK_y_7?f?xm?{8DJXnXv%|VaxksH(KNgS+eUdOO*I*ZIT|ut_~vMeZ7~BJS~B%<C79lSz?hya=SHmuL|l`}2m_kva1PnBRD&BM(^Xl;uR@>rYTB#ya)I&=RC^o7;$qsQ<$w|t2-yrpLmuoOYck}@ZeyT<SUDq}`eN?*YhVF}!GOlnyQu|8ZQfArIhMyZ@kMRoi_-YMjJRcIs%L&IPyAS&xO?-9+Qg{S#HeZJi)PkGniw^Wy&=TP&l3YGGrFXiA1f0-Hl?^K6R%mD7?ANr6I+AYWM))pZDIp~gQ5wVFhfHVG+~Bj!o5d+Q5ipwGJazR?l;X3r}?1k^}K)cqUVjPZw}E*j0yYZ*covr4TO#&$y{?*uITD5p$S8#$*S)D606o#a-Et)K)XeOM4UDhOe}SeS!Ifb6o7U2eT<G#q<IRnG8KJYifU2Blj0~vc_sx7*VscT!f+)IDeCZ@E5|9~aEFPbT?$!4j6J9fcRDk!iyS2c-%rg-jJ`tF<a!PrhIPQ7*wtBQ4Z>5uVpbU4cd(lkJn@%cU)3;tF6NW-)n<95q?)9FLp3P!@KhgDl;ad>$X)E9XvZmN2Sq+i5g$rX4pW336!n=DX`Z4Tr=T4a`H2*<jZXEiLjfMlGbobnA9{cyk2sVGiZZ0ABYsS$16FRex;#+TM^c9R8Lk~ex)7dX5D9T{NWoQ*kRpziYjLc7eE+4gN$G!Uk<tTQr1aN!3H|*tzG`o*k1scsj8sOy1(XH0PND!!&WG+A2W91eU3}V-5z62m<YApA#dk+LFrl7WbBq$){3<X8M74RdFJp0UY-H@k%BVr=Wny*~_9C*oW*Y&!Ikpj*2zM^(S2t%UMhJmNVj#rdGyZ_<070Cag``=8*}|$}NsGKT6=yFk_cejAtX`Hum6~Nnl}P{avb8Nqq?(BFPU}r9ni^lba#x&IAv)T)83k@LKa|W5CG$hJ>Y7Xmi%iKXnwrIE3v578vz4OR9Ku)oq2awAn$%z;WIysY*#F_On^#n4(^`<t11--Pp&X-uV{J?(5^WPiGLdMTEs}}!YSjdNf-lEzv8?b^;n$U|^eaL#W=E_<cv*8dJyK1ip<&y|$6zu>0``qCk=mbk2myX(H@EVPk%W-U4)A^sZirT{tRI(11xU|F5O~8j&O!RxY{I1Uj0qOf`$?gnVayl%8OD5ZPAV$TDV92-s!7{cWx$C8Cy%q4W77$NaBQ`X)-pM=Oj4V`BF+5mOFn?KN;B`5%YT0g(GiC}hg(@wLmUZPacF2}4*K1d3|uq?vUCg6uyZV^<tpYO*hO(~6aG!{d_SHZfLF^G)WJiCmjMnVmD2=X`i)B9G{EDER}XI%9#*^@!_y7V1Kc>lX@GyoU^=PeEFP|S@$l&2*XogZfSVi&P2ttV;{XqrEZ^lgo?5@XL7Y6CTF)Y3ygGOs;Gy-JCx}mRh$nvHCw}55e&Q#7;?KbcUgBwo_pfK(8w7C}ztEn9FS7UFx%m6OZME^<UY7h0Kc$h5A%7i;Ffi~HF}>=sh@ePNgkrEllI>`EQk)bg#Yu5eoD?U;N%0$}(As3}uP!;}uS3z0b>~qO(c~@b-4qG<G?bkb$a_`#-2v~GF@>nJmwg|B)KKw9VH`#x72?)|;lPw&3M^qgt*#wYj9Z6vCx@a7Ua<W=zzpMP!|F(JfC8G+iYcg0xND7Uzs4JwhOsSi^dp`Rk9jva48EieWcP^x;Bk_`90nvqH(<x?O<)X*9RGK(al1di-30m1A4&DiSu~BWkDySAQ0mYj*UJmBey6)`tC(k9?ateu`u%uJLAF;__4c^X`9sGY6zUz+l?{x;IM{(-0}5pSRE}o@3eq_N6-D)rg`Of>J0Eh7fm3Qu8K%hiAT=paUEwhWcO6D`g$tZ?W6C1TmBjsqv9G*A5%y4IIHh<(j#CskrFhEPuq1FBl?0Ba@3KJ=_E2OvrD#HCD2hQ*;FO{%vni^S2Fxj'
    'ICPgzSP=0;$D9&(7^@Pk&RFfwtaMJftRQOo*lqH9v!AaLs=2B!h>1slN34>Eax4u!Cq^J&yRN<8FqiAr_<&-6#A{!KmQ{({!Wa-$14C*~u6#az635x1-rj|!!M?n)5#kZm5F-5`@-Gro39wLjPn~*j^F|Zf535t4@BJH6lj=*py#aMQkkZ$%+Skg~=Bt>;)tT~Etg8Dls!dM<0Q>1B%a0dm=QaIVD;sYqcXi8@&(nttL6pIl4_ZA^Me}4Iyu0r^i=nLTyhb>h<T5K<U8`2j{zXsYwU;Y<!TTM}3Ch*+CS8*~!mGF~5XtvIXQGjHaoR~qMe(?Rp5!LiQ(meV&MPGgTJf?4e9*K#BVx+SzH0mTs2k4#CARVPIKpg?rn@bNC5DG7>_tTdtdcA-m3Q65dUyjm8FSa!wq;He-MT?Zti%bRd;gR$eD09@^HAL@-_IJ>?WAuc|nSjI=Tddtzq>oC%uJVB;Sm=7APlxG|$gaUj`kU-t<fd)pzXJ4aO#co>mtN@s?x6>Y0-!~3>48q6d1?kgpXTW=Yb)t4v>*U|_2^fS=IK+Pa0DwnG`+9>(3+3vDnl43%M1h6NK*9SPWo)>RIbl5aTUpZ^yJZ3t%B(nP?Vmg1A5Z*5%?HLdakT#wyuX1pRAQTJ$;&>51PJzVC2*19rP{eoMeTZYy=1B72A~@`Y)<1({dUVQ<Z}0vqN9iGx6wuujzrzN|0r+=~03gPu2AZdN*f&LoDQB`Z_~Tldk&VAbs@IZF}jlE$eI1=YfLWGlZfe^%y-JruTG^`7nKaBt5Fk=BX#2O^<T!ri1illAauTRJ`)p^wCqP0&FjRI7sj5Zo@tF>EZM!ZBKRd#?Pil*~}_e?*9F2q}0#x=3(^(D|ZEBROO-gY?_Fb!BI%|P(vG)E2Oc3!gMs^B_Eop8W#VB5MCe+|76BI2J}M`cLu$P4Bo)X!o&t0ZKunEhm2iSlU2nE>-WqX^Adk$pr<l!j1-N28cDtM`o^4USZ%ADS4Ny#bR8MiG}1$BX9D|zys_px8dUJm(bK@`g!qk-&jnn?;yN_r4g*!IF=T#YG%AjMvG=!;Z91oMU~QhLWAw{}cWs+1zBIH!+jhp(h8FYP#kq!7;>q%5Lrbw|+1y!AtxV9=du}ZJ;5XLpy0NtH#>zc6_NZkxLqii!Y~~f4c~vK9X10a*ArGHM>dgZNO=BwiVhksbo(6p=|6H2H)#XO5wK`m8Ya%n7Cdy=RxYF8inWfuF>I`~IQfbn}EnTHK=%~tBz}%$6_vd!5c{kQ4WitjHkqyomj(1}Tgstg1r**iSL7Q(ihHMX-aCY5{X3)Dati6#kc^PffWTfXc#TMhnlHvHyJxj`HE0302I=_?QHl6IW+E~)UHx`>|o$0fZ=F#~>w$+1Y_p|nU;pu~pjb6|#)>huzlk9}eKm`U0<|Zw8J&k5jHvEH&vLU?u{CZP1yc)^|RXgnKP?*`RdojfbtlQew@w`Q8MrUtPTV@?^m;vuSG~9W{6w%z7z(!ejQ4r2dZ|q5Us0l~L8he)IUk7V-R%1^~J1Cm5=MnVNGO7jSp(>{sS`lzFrmCkJyP=L*CR>G*XDJ*NPcbNx*0~g)B6`XlgCdT#Eqf>|ZHyRda+1j3v^5TerHA1+6a83XOHad`3kb8g-B6Psk6aBc4)fU<MJ(qys^xA`FhhFt1-VM5pt2dW$C1<H^3&y@vL(%kc=P(BdXysU(HxESMq`Sxpng)E6eq<=aZ;QVvlM&c5=W7ow&HQ1n2pb*ScLF@xCr4ff7B&;z2rrWuU{@z7QGNOuk1+hijIWfl^nUEgYY;THH&rRZ;6^2WWsT@PNGO*$m)X_{Fd|@@K9~p#_6ZlHWI-%RS42w7J#By3VX=WD3FOzpr=DRf$FMU5lX<}Ab6-VWG-3(wAeSqz0TD}m%JOgR%$ec9K2{3j)G#nFyq)d%<SAyaI?WgKUa)9<awziP44w!FB;vW$VY$Z8!EeRC_Vp%p7#vyxuNizzoGLjx$}lTyEoL_AvbSP#pc}*HSdN}^KK|LcgS8`eAIQ;gNO1VSLcROSIH3#*+X^B^$ZNa@GYUH!j)W9n1qXcL$@(nLzYai@Knv_4Ut9zKn-h969t>4#X6gd>V{gm=RSUjtRXk^hSCjf&136bG#*5&Cy0Dg)E4EO6eY<;<0!pJaRpEhl|_2xhx3Qz94?ac>qk|Q#ZCTQdVY-;$(bz&SH0loh|2qv-oBfU`9a6@K+c0qxA;c=rExRuH0<F}V2niS3{UEO5$j(&!^24>8CIa=kJ`;Rd^$Lv3&UhSi6XDNcE451ycld7)y@Voz5!z*7YS>KJS)?fI7iu!d)R!d0xV)I@5ERr7CjcLs&N1-0Baa)UmMFhiI<1bH^j)o%88xW4(vNy*Hf5G$lbrwUjci_KDYyW#$L|Ojy8{>Q|&RQ;qLQRtdOjj1Rslgc@2T}BBbPPisYRp`K2OxC;1zMdABN9JT{o^QU_jcU!i%-+;gIuS&SA>TVM<>aqnCdESaOtdr$D}4zEA(AG1E__-c9HQMLrgKDEeIv6rhpf5=sfSMVMg&yx-vsgnkgI9_sDujr;1^H=sthvZ-rDnHMat~df`*|jJ<_2b+cEIZaNIoRy0QXI>Cag5BxF|`--rG?2BevdF>ayGznFfr@-MWNqfSRFq16FadJJFycxu@gJ7J29uO0?l$^RwSyFOiVw!$772u^V-WY`D!D2<Fd>!)FOMvf6pJmP5R>0&~cO3*p-F`Omy`gUvN0(Y<?w9S!M(mnm?GJ)28ukv-xvIaJCwZho!b_>CRx$@=7(VwwcQoFqNh@y)#VuDD-JFvnA*CMYRMLQ6kL^%a+U;ow|Im-rkB8Q^q9}X1y9lK;65-9aZ*X&|xxbOqLmd8O6p}gxGDK@*ylFfX(JnoKauQV0oXN-7N=`9DP?B+x0!ojhBeZQ51P$hh^u{;;QWSW*JnbeG_xkXVp0!i-To*n03D<FFC=8{T;++D-NmZVXhk|I3U;W&;=2<h<uG%g%ta*Oj>hg#f?*A*)gP6tFOLMEDxTfW6}F-kxG>9%_4zFLBqQK1e^tay2!u>c1KZrpy3CC&g$T>4Z&d>94@6!F|}S9>G&{Cq)cJW#-f9fgL##<9R}to<C7fB5d*xU;^bh-!R)Xg{Bza$x$68}b$;$BX4+p;J7%|WefnIFzU0*!&o{dhAz3YOS&i%?ARY4Oi;kP5<5%tl;ipMozdUaYNsb?&BgaKYjw1(iEG0+fzdf>HbvF6B;{eEp<FXQ-z|oiB;gBJF-JeqtVN$R{uT%n9HZd(&b(pNiRS_2TK~;8OeFR}PF;Z9`iWhcZ-Q#-|n8%&&XOwBgxi)9}@dB00m~%y#r<%$(6YZsy&BqM$ZIE6!e3jkx*bW*GYP-_BJ-Ir&tHiREag3U+kBy^g^COZxEX^p6>pm<V#DW)*^$aZiim>_}Vda6?On{$<g)v4>O;wcEt^h$gD*dOHzB1UP35YAkA)bI3Rna*klwC;?N{I_AyAo4QBEhi0GrafwlM1cAov=*YWo}f_`xPBX-Sj3HZq}};=H+tmws>+3C~it;H(8h`qeX8uV-?sUJH1W$?4{9H?<fa@SM@_xzdK)cZ|caw(m`zMAkK~nFz?}sT&zv;QhARx(!<i671JyH<{6p+W<G~LA$nFrDHawl<swWr(!<O(k^0oTSq;U)E(SCMBOf!@C(pT_)ldv9@|3z+{oDa8UF(KoTXM0mC@QvRtrXskB_7cr^wY({R2uiJ<$jD+6H5-J?6)ABH^$68i<I^;tDztahMY;euU9Z#V<edn#xoRz#Scvm!nBE8$Z{TL$4om(p_&^!9uHz(_;&gsu<{*Y`Kx1(;3rP(#2$n>44SiWZEgBKdul$8Ewap~PL_EMS3A%vh(E&Sem*isd)j7|c^=m0vGM>cIy=u%jGX8GAgn%Os?+1AGqib6$D>mnCb6T_c@*=fx*oCux5HRIf<-44sgKn|pCiXsGj_~!ecARp62r0=JLU5|nP`He?TYP~;l(pg$N5$5zD3?fR~}$z_I#I<<C4+#V4kN@a}HD&%lBfg1GYwsV{|Ldf+~&{sXAJ#y6cs3lQGhaxoWRNtsAxNdAQQp<+R$SW)~}aJ!>XR>HE#>@h)tN<I}z=Rk?BiEa{vC1zXP*Rt?*I1l+V?<d4cM#Pc|Fa}qbH6l3B^HiUV{I^Pno*}$3LnIm8V=`Lx8wUQGo!M3K*$ohRO`YXA~&obv%nO!@$5$E%EpmJ=l+G*9i#f{AWEi%{VUgnBdnTsr$i?YKadEA<p6T<UY@w~;Iy<oq~O&YnhJKyMSbl=U#>h9h6U@(GXPK?f1rej}8cYUQ7p-~PROZT46^!T`y8QZKUk~lwCcVh8i^w1N`#NO`dMRn3ajJwJtC?Qm^_w*PUUiTHudWVtaB44%3SC`~WCG?F@=`NgMi%t-;VWgP$4b$i6iv6Oo<f!0NvpwMtVAa8zlFvo@CO$F`<A!~Xk%L7C<KBKduyik0HAdeN7N3o!uZWd9FuE5j+UX`f7-Oq-9;*N&xeJ4>s0=ZJSRP^#V(2^)f<MAw#DKsEY(5#W1@heLZdWlt-Pq#LH4j*bATPH4psBEfZhLWFyW}XB^21~@k7;tf^`ShLdU@=P=dFld?Jl=+S3ar{&yGgCc-nFg^J5LLD)T6o9*Nb1SQ%q&FP5Kxg&`LAV)Y4F8Dr$!`a`jBAC~M}-zr*wmsRUV$icXKRdKLvSniMsCtE5Uj;Z899R?g54J<KC%5`1M^y*+re`nQN@3%K)7bH6cK(DSu*yg^k^Yvsykro+dJ35FA2W%H65LRlNdF>;i`B-uMG0MRMAv@YZC!Wp4oM9fpMqzhHFh`3S4`QBvIE}EdTca9AMj21HdjK28TJFb=+M_(JY8ok_kLF`}Ml|exvtS!4ls(Px!K^r*`uC`6_-JCE-I=4G5Sufhif&=2ZkP@ltta%xWvAYFMyLG9tW!w%TV%C7k+)*(8|2oS@}hcLn7284wo1n%W6kuGjPSWmkD1|Jt6Wi03N{s=P|~24lsY@ZNftk-%<<A9&SM%YJ`g>OqzPQv&L^;lyms;!qk~ww3(LE)2A+zG;k}rEnCf8}@eN4KG7@z#o&rhbDm@W+()`tm&}P#WMJyU?YSD3Vk-tW48;IDpbou)|c*7<=+8hr$*JID~%JZ_ufQlgagI<V+=U$hb4|-X*yi8uM4_$M<)JsN62c7-gA0!8h`=-rP=gmE*w96~8-@kt`u!{(7q%Hmsg_EUxssSg{C9W%1I=~`lph|skg2vB`-hF=hk%LK9HG5n<?@=^%4S+FoG8vAk`b6bim6XrO!J>l&X-_Sf=QpqlF?s?Phgi8At5_oSu!ONNg*7aU(-4!1XbZ-YG@VKB=!`i>efDErL()!=!gN+3mlvDEt!X8Hg+eG9Zq%^us^?+t`N0S0G!`G67a#g>bwU!#oE~VAoxUL1iTfSWNR!|v5h{)u&rf%6-g+CP!UrEK!RCCRP@SZ+0n{)g!wj2|(^wK5CNTRV>A!bci-@5XSV7u=2F=<9Fxzn&OVIpYz*3xPWnlboj)C8BIT>N`0G72&#@*OGE+Aji#pM}To5jkv#|SWv55w9%EL#3&(^%2`CqGaOj4x&Bm#2;;&!3MDV$s3)*&wROvB8kxAjy0rixP5F^|^ikWcn9mmG`KByecPB_dN<Duv`J>qcKuXr2@m{Gjh$f3G4~J!}TDxSB*V`?bXuXSs)?rG&J1l51;p%d&Xv)Cj=Ml4uLpY#^IoeZ)k1YAHa7oiYAThm*L^RmUr8w)4-gacN_9uR||5((H)0ACmp--x5#6E<Xs-4w|8+Yyj=eC)6)58-#g!y*3T4P-Y@8yj3aT4e9>l@s94XU-WtFFXK_t{F_qT|Fn*7`o*9ER{-8Z|tC|yK45`R9=H{ohJeQZ{xqP}jm-zC2@i{*Exdh|6<ca4}?wIo`k5It0Rdt|fhi_nuw62r%BFy?a%4_5#B(AG*-J5%QZBv$<lD>xJUx=G6yS=8b!_r&ZGTL(PB8MczEF-;HrrV0%%nj;KE*sRRTb|SRtB*9N+X9`vN@B(NSB1SO_Elytm%I{3l66(ZRWh!MxFU9yC$1t>t=LzrIGlIYyOE+R?cIp4g1S2Y&cE;eZ`q;#^S}M~E5EepwBMHSjeHH=;6if+D(-|GW1<d^%u-_OudUM(oT%-<wKn$&-KQ3ubXWyowyo<Vt_$FANT@6N>j173_vL|=((Dr$p1NsF!Ut2q4-x-lXZ7w+&bwIs^Y8roE$`7kzwgkW(y~Lp<(K!1x6A&V%;2wINBjIc|NQsjcMIo|m-iySE-yuXTltm@1X{(nRCUxxoy?#}Ep*cSNpr4yGwCy~XU1TTpR}PXWA>-76<L5%ApVA5+jG5ryY;s01Am_F179wFIcg&iL3ExQJ#d>67RiE)Q@jOyt8pu0Q}okX^CNTbk5E{1Ml&d8m$Zj3ewEHYYhLt9&W~Bi#aYSKTf1KC==$V7PTV7idmQu99{dI~T%buWP#lwi+$O8hN~%?i7O7TtTFkyyElXUIPRzW;mk+b`aTkYTtvV8^gn0zR<3DB+iX_{K2XF9LFqeV+<BLD%+tr^ly)2h8ep&rFy>ub)7_na61~LPnY@Xb%Y9wmUHVq*sl4#XN2-alB&54IS5arFQBDa(BT~~oVK?mIxWvA9dE;65a)QNAi+zd$<ZqD+Vf!oS50#Dyo3pyxDrFE4w=t*#U${Y<D-tK%aR37+M)8ruySYR?ZAcCCcGDTnn5mu6hCTP%mQ^mQLKv7&t)5bIr72Xvzq;i%Vqe&<ul%RoydlXF=(ZmTF0$D&bO&QXp2^vtC4$z=&m#vLBL8ER9&?F=Au}>2@O-6Mf)O!j<W<aBTZRDOn6Evs{29xNjdT&C1J7EplG)hEndnVKbC>pEGa#{Cs+APcFS&%yOQIK32-MnqL_<|}o@zmXxN<e!ZbbnjQyEAS9tG6LH!{hWes&Y%dqT{;z1@^%)CKwBMTVS2rEaD}W-m7~@L?Ma!`rc6IZ%{OEL$}$iie}}J=r-gU%=`iAmN%~k(=%<otzy!|^?pjQ9OJgzD!~fMS#N8jDR9U`n%tdHINQrssxn(Nkw;7$G_`+mVg795G!aKll?j?Wr0L!p?m;4NYeZ9rG&DhzI=?oH#`b!V?59f;Cupd5^D=45kS0ygFj3m12_u>~K|@RxfY%18gafFEne=4SG+fe$G*Kr$h&m!v6&+Xa7fsM49(M`%gv6r|APq?JKssT7;><OTRz)O7v}4|6hBTTwnhI~rIxjePK<harg?x45M<r>><Oo$2vmzjpCG%;q16BxXxQZHhZ^QvBg)k)a<M)PtQS~(pQx?&VWYKH<u}hq4yy!KEUY5)FiRbu9?c@K^--&%MSQ_OCbHj!FXky5s8y|Ecu*po7a$CF6PSS)mU+Gc`9jCWymvZMYEmr*410Y5p<$&S5r4K%Poo^AopRX8!6eBk*g487Iv-L1tMWL>kI5k?2MP)?Uu%KA|4ofo2K!=euD|A?tsWmz*$V4bTmTJ&K7g+P{9xU(1Zcog{s)IET%MMl?ta(^_3RWEKW2^?&+F>j^m|JnNI+$Av)hlz0igCeh(8~*Sw5%fSN<=hQ%Fr!y=w(H6QZ%`Vrj8EOEh?Fufzqy2THa%F){|FmxlJ!baxn3&**S4@us^s93mz67%q-u1AC?@994vTPaxikRcn}L%dvYI^23V)bEG8Cjy6p{<&fgGQbFyeGu4=ap%bcBn7_DNZ=0k3xVmB{UDj`jb^F&2z?K_P7NNjw8VtYEifOJN&+O0E{jILXsx^U#iE2{0IuJ1#&&T#8I0&694tj=yp(aFN(?kv&E!bHvS>?POhcjKo{+3*L#E`de=?mza~vc6oiWkpb>GmR1txK)nzf{XS-4bB1|O0xJDX~=BCLVZzWQByo)AM_--CKW){jih%bl_}lWmczfYLY)*7Y()W0(hh)CZn63YWTJ^AJS3DSRuwy}a#sjCjfTdsUzVH+QXY*}$oou~Lkc(oysQ`|lK`@bsnz$$ikdUkHuqxBEPwgH(wL9NVE(2b3=>>~tvB3>wG;bcv0vS~&d%E1iO~#J9*4zeVqQklz1Y2}(H>dLcxp56l~wkklT;ncUcp{1qYNp&fXAF<gUxL=7MtQ<wBfoRjN%&uuJ>6WXCSN|AXi`!kFWwJj|JT;hiILbN3DylhOd5xFg4pcQt$%Myz;nCiwJBVsyhsC{^IAVr$w^*!~cNN5WjK3Dh-m8`9))#bjiMe--07=dF5R^WrJ%Kn3lynC9b2tk9+j@bxwor99Ld71P>$D8PSW`d&d-OT_#xPqsX03E0P<i9n!e2k'
    '=;Tk)@5y$T6+|hmFEU<>`1z#W|+aq#Z<La?TC}~)Aq37V(l1~o`4Z5oPNWcd(g{lp9=7PEZax_PR#SGaIrLlc`B~z@Gq{dwV?pO?;bN4CUBR#wIyCUS+7{!(HeSQ5?4@?Fl8H)dp$d&Ft_kQY-6b@9}Bg^04xG$d$mj6FsKL%suXIov8XWN*CX6#x?i^fB4e||BgxY21yzZ-IXA1!;2F;!jV$JKmUa*G>K*N4MW!&X*ppWzs@Yg{FmkZuU||0#&gN9?pHm_i!kUf2y>OzocXF_1W6{BmR;6z?79WavsfTS(S`Q=71J}cn6Zd<`a<&L-f9_pY`}}sx0Q&jungNs#4n-C??dp!7%v$NVjRPd`K`=2qx_fwe&+zV_t-5Qr()Tu74}O?md$!J{e=hxV>HmPU)xPCyEhp=rTC+aI*Gu}hC4EPCvi4cIKSMc+W%Q<I$VC+{k;wcmGQ1HZTSa6J2NlkVk-gl`WZodJ!&zu632Z@fP#b4+chb|M#PJch5lVrJgl9<B29Y4O2;iE;bp_YSxNgpM(KeWwYnr{z^VjJ&a6LUIgSp-Nyn?)*N%C9=>y0MXt*pNQ-v#MbTL$l!S;!#?DH>fz;Z}wA2eyY0-?|Fa;s}4Nfc7*p_PxLZrV89kdEEvhvk(ty&2VpzNLw$@2x7{y49}X-ABb<46YNjp6YLcqT+#fIG9KanTW$F8P0%PVC!ZaB<ELmXhh!`VQ91;kaZ?LdSi-7t&E5<vX}k3r);;gJcU^!IGC3Pk1K09keDqFxXxFX3((7-`A&{{K<n^d(L2?epo%~td!TwoA5gbml7}pbw>`YmrJZ86daqSlK&jkTPp4caf7!plj+kb{<4HKSTxeWG4m(29>=7{os6<=>@29(jJU^7%gnsBcB=B8&}YPsqbH;wWZw+nyUmN!me-gWL)wB}1mlap9A!WMc)!i66Aqls35Eds3!TM@JjL!})PfO553nOmvNW^RqUTEVa}dg)n3`c%JFO!bi8;`xB)TU=oier112h9DQbvLaZ!1-=jPtwQe~!S@!m65I=(*P0)hcYgu-b5}TnQTl)x(L3x7SWc?H_<mC5Pq&lm{i;8ynvu{^I@dtwAROK}j?IUzdzM)n8?>?Ax$4nIZ5S?$*Ab@;&-Gn6(<9I5K5KUof<L>}$QDtR`(2Wr#=t+Kb$QOJ7VqS1SrqFQ8ca94eVs^@U6C;vCobIAi&7R&_u_<xX}%Z6vl~^Cp$k*;G8(|V)rKGI1AD{KUVR5Ud+Vr|M*hRNH;=ZN2puCL^hS)nzk7vST|vDSZi{H$HMAO0npqq(h$9f6(;M&Z4SRaezgcF>INl)(FtNQAxK3-BSkuu>VU)p-$)DTPi^HY9-`@N0c+dR0yH1^Y@_3aP*^9~Y->$+g{U?^_99oqk%cV+t5Ul_l_jpB*!2FgtbeVIqB<NGN_@nTHmr57~lv|Ie=N6+Mkhq43ncnhS^(t!^Tc&U$6}n5YeRnc$Mk=DL)D?RuD!!HbDAL!Y$TmfL97UO;FrM5rMcqM>tv7N^k<FDnPf^S_N>UV)qFS417gbK9sK=Z}QA0V6VzkRJK-k=0sEu|p8hr)ZD(i4F9d5{ZNHIJYgu+>7zv6F%rI4rwMPvhset-ZQNH%X5BtVfdr+Rux%sP2Ft&~*^4@6Ul07~Z8fgeA)(Wi()C(tA}YB>W69bF(OKt@dhsfW0%N#L>Z$4ekAn@5kTsGZgtf4m7u(fsiy9Yb6B<4s!GR{2T<Iom1^bWJ*{ruL7oa*CDT?B@(b*i`;XV2Z#fs(fsfzY;?Vq<gG#A*m3eYU@|}2sylG_Hq8cCPb`gph2-UBneu|P}WuPS`<T9mAr9eQ~kmWYS9b5D&{~EH0Ie9XsAi=a8}$^wuUOQoq&OeFxKShtgV3%*lH~bYgXll-1x1EhblJgG#Q}E2Vzr{Aw`9%dqhF@mlzbksG+JPwWFa{kg!799`ySyIVtjE&#Gu+b*-LPG9Rz9XXtgNBK(Uf>yARs9D$SZC>A%jXbb+#Prv&|UoOgm^!D<8kysv&WXj!V|JnZ?_FJ3SkKTVi-?RS*?*G33E=jHa)8Y*Oc{vC_rI+`M_kVx7p3}VugB+aIF<zyXlj+m@Q(mM+lJbwdCLtC-`g&#z*7(^yk_x1+YOdHEM$X6A(*}895&wmSnG2US{N?5S;?qYh@mcBMN9#ZTejR`3`aJ)B1N-wI{K5YZ!RQn_'
)


# BEGIN ADDITIONAL FONTS
# Precomposed glyph masks for the edition date and newspaper body.
# Copyright (c) 2010, j. 'mach' wust, with Reserved Font Name UnifrakturCook.
# Copyright (c) 2009, Peter Wiegel.
#
# This Font Software is licensed under the SIL Open Font License, Version 1.1.
# This license is copied below, and is also available with a FAQ at:
# http://scripts.sil.org/OFL
#
#
# -----------------------------------------------------------
# SIL OPEN FONT LICENSE Version 1.1 - 26 February 2007
# -----------------------------------------------------------
#
# PREAMBLE
# The goals of the Open Font License (OFL) are to stimulate worldwide
# development of collaborative font projects, to support the font creation
# efforts of academic and linguistic communities, and to provide a free and
# open framework in which fonts may be shared and improved in partnership
# with others.
#
# The OFL allows the licensed fonts to be used, studied, modified and
# redistributed freely as long as they are not sold by themselves. The
# fonts, including any derivative works, can be bundled, embedded,
# redistributed and/or sold with any software provided that any reserved
# names are not used by derivative works. The fonts and derivatives,
# however, cannot be released under any other type of license. The
# requirement for fonts to remain under this license does not apply
# to any document created using the fonts or their derivatives.
#
# DEFINITIONS
# "Font Software" refers to the set of files released by the Copyright
# Holder(s) under this license and clearly marked as such. This may
# include source files, build scripts and documentation.
#
# "Reserved Font Name" refers to any names specified as such after the
# copyright statement(s).
#
# "Original Version" refers to the collection of Font Software components as
# distributed by the Copyright Holder(s).
#
# "Modified Version" refers to any derivative made by adding to, deleting,
# or substituting -- in part or in whole -- any of the components of the
# Original Version, by changing formats or by porting the Font Software to a
# new environment.
#
# "Author" refers to any designer, engineer, programmer, technical
# writer or other person who contributed to the Font Software.
#
# PERMISSION & CONDITIONS
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of the Font Software, to use, study, copy, merge, embed, modify,
# redistribute, and sell modified and unmodified copies of the Font
# Software, subject to the following conditions:
#
# 1) Neither the Font Software nor any of its individual components,
# in Original or Modified Versions, may be sold by itself.
#
# 2) Original or Modified Versions of the Font Software may be bundled,
# redistributed and/or sold with any software, provided that each copy
# contains the above copyright notice and this license. These can be
# included either as stand-alone text files, human-readable headers or
# in the appropriate machine-readable metadata fields within text or
# binary files as long as those fields can be easily viewed by the user.
#
# 3) No Modified Version of the Font Software may use the Reserved Font
# Name(s) unless explicit written permission is granted by the corresponding
# Copyright Holder. This restriction only applies to the primary font name as
# presented to the users.
#
# 4) The name(s) of the Copyright Holder(s) or the Author(s) of the Font
# Software shall not be used to promote, endorse or advertise any
# Modified Version, except to acknowledge the contribution(s) of the
# Copyright Holder(s) and the Author(s) or with their explicit written
# permission.
#
# 5) The Font Software, modified or unmodified, in part or in whole,
# must be distributed entirely under this license, and must not be
# distributed under any other license. The requirement for fonts to
# remain under this license does not apply to any document created
# using the Font Software.
#
# TERMINATION
# This license becomes null and void if any of the above conditions are
# not met.
#
# DISCLAIMER
# THE FONT SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO ANY WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT
# OF COPYRIGHT, PATENT, TRADEMARK, OR OTHER RIGHT. IN NO EVENT SHALL THE
# COPYRIGHT HOLDER BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# INCLUDING ANY GENERAL, SPECIAL, INDIRECT, INCIDENTAL, OR CONSEQUENTIAL
# DAMAGES, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF THE USE OR INABILITY TO USE THE FONT SOFTWARE OR FROM
# OTHER DEALINGS IN THE FONT SOFTWARE.
PRINT_FONTS = (
    "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"
)
# END ADDITIONAL FONTS

@functools.cache
def font_data():
    inherited = json.loads(zlib.decompress(base64.b85decode(FONT_DATA)))
    newsprint = json.loads(zlib.decompress(base64.b64decode(PRINT_FONTS)))
    return inherited | newsprint


@functools.cache
def glyph(font, character):
    advance, left, top, width, height, bitmap = font_data()[font][character]
    rows = bytes.fromhex(bitmap)
    return advance, left, top, width, height, rows


def text_width(text, font, tracking=0, scale=1, squeeze=1):
    advances = sum(round(glyph(font, character)[0] * scale * squeeze) for character in text)
    gaps = max(0, len(text) - 1)
    return (advances + gaps * round(tracking * SCALE)) / SCALE


def wrap(text, font, width):
    lines = []
    line = ""
    for word in text.split():
        joined = f"{line} {word}" if line else word
        if line and text_width(joined, font) > width:
            lines.append(line)
            line = word
        else:
            line = joined
    return [*lines, line]


PRINT_SEED = 20261121


def print_mark(x, y):
    number = ((x + y * 1031 + PRINT_SEED) * 0x9E3779B1) & 0xFFFFFFFF
    number ^= number >> 15
    number = (number * 0x85EBCA77) & 0xFFFFFFFF
    return number ^ (number >> 13)


def print_field(random, step, strength):
    """Interpolate the uneven surface of the sheet or the inking roller."""
    count = SIZE // step + 2
    grid = [[random.randint(-strength, strength) for _ in range(count)]
            for _ in range(count)]
    columns = [divmod(x, step) for x in range(SIZE)]
    for y in range(SIZE):
        row, offset = divmod(y, step)
        top, bottom = grid[row], grid[row + 1]
        blend = [a * (step - offset) + b * offset for a, b in zip(top, bottom)]
        yield [(blend[i] * (step - dx) + blend[i + 1] * dx + step * step // 2)
               // (step * step) for i, dx in columns]


def chipped_edge(random, corner_depth):
    """Layer shallow frays, broad notches and diagonal losses at the corners."""
    anchors = [random.randint(0, 3) for _ in range(SIZE // 7 + 2)]
    edge = [(anchors[x // 7] * (7 - x % 7) + anchors[x // 7 + 1] * (x % 7)) / 7
            for x in range(SIZE)]
    for position, extent, depth in (*corner_depth, *(
            (random.randrange(SIZE), random.randint(3, 18), random.uniform(1, 6))
            for _ in range(46))):
        for x in range(max(0, position - extent), min(SIZE, position + extent + 1)):
            taper = 1 - abs(x - position) / extent
            edge[x] = max(edge[x], depth * taper + random.uniform(-.8, .8))
    return [round(depth * 2) for depth in edge]


def edge_weather(edge_number):
    """Give each edge its own bands of oxidation, notches and hairline tears."""
    random = Random(PRINT_SEED + 37 + edge_number)
    tint = [random.randint(6, 41) for _ in range(SIZE // 44 + 2)]
    stains = [0] * SIZE
    notches = [0] * SIZE
    tears = []
    for _ in range(21):
        center = random.randrange(26, SIZE - 26)
        radius = random.randint(6, 33)
        strength = random.randint(19, 66)
        for index in range(center - min(center, radius), min(SIZE, center + radius + 1)):
            remaining = radius - abs(index - center)
            stains[index] += strength * remaining * remaining // (radius * radius)
        if radius < 20:
            depth = random.randint(6, 14)
            spread = random.randint(4, 10)
            for offset in range(-spread, spread + 1):
                taper = spread - abs(offset)
                notches[center + offset] = max(notches[center + offset], depth * taper // spread)
            tears.append((center, random.choice((-1, 1)), random.randint(12, 27)))
    bands = []
    for index in range(SIZE):
        cell, fraction = divmod(index, 44)
        color = (tint[cell] * (44 - fraction) + tint[cell + 1] * fraction) // 44
        bands.append(color + min(68, stains[index]))
    return bands, notches, tears


class Newsprint:
    def __init__(self):
        random = Random(PRINT_SEED)
        self.clouds = print_field(random, 93, 17)
        self.mottle = print_field(random, 23, 10)
        self.pulp = print_field(random, 6, 6)
        edges = (
            chipped_edge(random, ((0, 38, 22), (SIZE - 1, 28, 17))),
            chipped_edge(random, ((0, 29, 19), (SIZE - 1, 40, 25))),
            chipped_edge(random, ((0, 25, 21), (SIZE - 1, 32, 24))),
            chipped_edge(random, ((0, 26, 19), (SIZE - 1, 31, 21))),
        )
        self.marks = bytearray([128]) * (SIZE * SIZE)
        self.foxing(random)
        self.fibers(random)
        self.edges = []
        self.bands = []
        for number, edge in enumerate(edges):
            bands, notches, tears = edge_weather(number)
            self.bands.append(bands)
            # The footnote descends close to the bottom edge.
            limit = 10 if number == 1 else 14
            self.edges.append([max(base, min(limit, notch)) for base, notch in zip(edge, notches)])
            self.edge_tears(number, tears)
            self.edge_foxing(number)

    def edge_foxing(self, side):
        random = Random(PRINT_SEED + 51 + side)
        for _ in range(71):
            center = random.randrange(8, SIZE - 8)
            depth = random.choices(range(3, 27), range(24, 0, -1))[0]
            reach = random.randint(2, 10)
            strength = random.randint(21, 54)
            for along in range(max(0, center - reach), min(SIZE, center + reach + 1)):
                for inward in range(max(0, depth - reach), depth + reach + 1):
                    x, y = (
                        (along, inward), (along, SIZE - 1 - inward),
                        (inward, along), (SIZE - 1 - inward, along),
                    )[side]
                    distance = abs(inward - depth) * 1.35 + abs(along - center) * .78
                    scallop = (print_mark(x // 2, y // 2) & 7) / 3
                    fade = max(0, 1 - (distance + scallop) / reach)
                    offset = y * SIZE + x
                    self.marks[offset] = max(34, self.marks[offset] - round(strength * fade))

    def edge_tears(self, side, tears):
        for position, direction, reach in tears:
            for depth in range(1, reach):
                offset = direction * (depth // 3 + depth * depth // 180)
                offset += ((print_mark(position, depth) >> 8) & 1)
                cross = position + offset
                if not 1 <= cross < SIZE - 1:
                    break
                x, y = (
                    (cross, depth), (cross, SIZE - 1 - depth),
                    (depth, cross), (SIZE - 1 - depth, cross),
                )[side]
                # Reduce the line to a stain where a top or bottom caption is nearby.
                strength = (reach - depth) * (21 if side < 2 else 62) // reach
                pixel = y * SIZE + x
                self.marks[pixel] = max(34, self.marks[pixel] - strength)
                neighbor = pixel + (1 if side < 2 else SIZE)
                self.marks[neighbor] = min(152, self.marks[neighbor] + strength // 3)

    def foxing(self, random):
        # Soft, torn-edged stains have tighter dark centers and broken halos.
        for index in range(690):
            x, y = random.randrange(SIZE), random.randrange(SIZE)
            if index < 260:
                y = min(y, SIZE - 1 - y) // 7
                if index % 2:
                    y = SIZE - 1 - y
                if index % 4 >= 2:
                    x, y = y, x
            radius = random.uniform(1.1, 4.6) if index >= 34 else random.uniform(8, 23)
            oval = random.uniform(.65, 1.35)
            reach = math.ceil(radius * 1.6)
            darkness = random.randint(19, 42)
            if index % 5 == 1 and index >= 34:
                darkness += 31
            for dy in range(max(-reach, -y), min(reach, SIZE - 1 - y) + 1):
                for dx in range(max(-reach, -x), min(reach, SIZE - 1 - x) + 1):
                    gap = math.hypot(dx + dy * .19, dy / oval) / radius
                    gap += ((print_mark(x + dx, y + dy) & 15) - 7) / 52
                    core = max(0, 1 - gap)
                    rim = max(0, .18 - abs(gap - .87))
                    index_at = (y + dy) * SIZE + x + dx
                    self.marks[index_at] = max(38, self.marks[index_at]
                                                - round(darkness * (core + rim)))

    def fibers(self, random):
        for _ in range(16900):
            x, y = random.randrange(3, SIZE - 7), random.randrange(3, SIZE - 3)
            length = random.choices((2, 3, 4, 6), (45, 30, 19, 6))[0]
            rise = random.choice((-1, 0, 0, 0, 1))
            tone = random.choice((-9, -6, -5, -3, 5, 8))
            for step in range(length):
                pixel = (y + rise * step // length) * SIZE + x + step
                grain = tone if 0 < step < length - 1 else tone // 2
                self.marks[pixel] = max(0, min(255, self.marks[pixel] + grain))

    def rows(self):
        top_edge, bottom_edge, left_edge, right_edge = self.edges
        top_band, bottom_band, left_band, right_band = self.bands
        for y, (clouds, mottle, pulp) in enumerate(zip(self.clouds, self.mottle, self.pulp)):
            stains = self.marks[y * SIZE:(y + 1) * SIZE]
            shades = []
            for x, (cloud, fleck, fiber, stain) in enumerate(zip(clouds, mottle, pulp, stains)):
                top = 2 * y - top_edge[x]
                bottom = 2 * (SIZE - 1 - y) - bottom_edge[x]
                left = 2 * x - left_edge[y]
                right = 2 * (SIZE - 1 - x) - right_edge[y]
                margin = min(top, bottom, left, right)
                mark = print_mark(x, y)
                if margin < 0:
                    # Shadow under the torn lip, fading to the exposed backing.
                    shade = -111 + min(128, -margin * 11) + cloud // 4
                else:
                    edge_band = max(0, 96 - margin) * (19 - cloud // 3) // 96
                    if margin < 64:
                        weather = (top_band[x] if margin == top else
                                   bottom_band[x] if margin == bottom else
                                   left_band[y] if margin == left else right_band[y])
                        fade = 64 - margin
                        edge_band += (weather + fleck * 2) * fade * fade // 4096
                        # A broken tide line follows the broad discoloration.
                        tide = abs(margin - (7 + weather // 4 + fiber * 2))
                        edge_band += max(0, 4 - tide) * max(0, weather + fleck - 9) // 27
                    lip = 17 + fiber * 3 if margin < 2 else -max(0, 15 - margin * 3)
                    fold = self.corner_fold(x, y, fiber)
                    grain = ((mark & 7) - 3) // 2
                    shade = cloud + fleck + fiber + stain - 128 - edge_band + lip + fold + grain
                # Keep the extra weathering in broad tones close to the edge.
                if margin < 64:
                    shade = shade // 6 * 6
                shades.append((max(-123, min(23, shade)) // 3, mark))
            yield shades

    @staticmethod
    def corner_fold(x, y, fiber):
        dx, dy = min(x, SIZE - 1 - x), min(y, SIZE - 1 - y)
        if dx + dy > 68:
            return 0
        span = (33 if y < SIZE // 2 else 47) + (9 if x < SIZE // 2 else 0)
        crease = dx + dy + (dx * dy) // 115 - span + fiber // 2
        if -3 <= crease <= 3:
            return (10, 20, 31, -36, -29, -19, -10)[crease + 3]
        if crease < -3:
            return -max(0, 23 + crease // 2)
        return -max(0, 9 - abs(crease - 10) * 3)


def paper_colors():
    # Derive the brown patina from the theme's paper and warm ink colors.
    stock = mix_color(PAPER_RGB, STONE_ORANGE, 2)
    return {shade: bytes(max(0, min(255, channel + slope * shade))
                         for channel, slope in zip(stock, (3, 4, 5)))
            for shade in range(-41, 8)}


def abrade_ink(mask, left, top, right, bottom, seed, large):
    """Press clusters of paper-colored losses into the fat strokes of display type."""
    random = Random(seed)
    area = (right - left) * (bottom - top)
    for _ in range(area // (45 if large else 47)):
        x = random.randrange(left, right)
        y = random.randrange(top, bottom)
        radius = random.choices((.8, 1.25, 1.85, 2.75, 3.6),
                                (20, 35, 27, 14, 4))[0]
        if not large:
            radius *= .62
        height = radius * random.uniform(.58, 1.15)
        tilt = random.uniform(-.65, .65)
        shape = random.uniform(-.48, .48)
        opacity = random.randrange(67, 101)
        reach = math.ceil(radius * 1.7)
        for yy in range(max(top, y - reach), min(bottom, y + reach + 1)):
            dy = yy - y
            for xx in range(max(left, x - reach), min(right, x + reach + 1)):
                dx = xx - x - tilt * dy
                scratch = (print_mark(xx, yy) & 7) / 23
                cross = dx / radius
                rise = dy / height
                shape_distance = cross * cross + rise * rise * .86 + shape * cross * rise
                loss = round(opacity * min(1, max(0, (1.13 - shape_distance - scratch) * 1.44)))
                pixel = yy * SIZE + xx
                mask[pixel] = max(mask[pixel], loss)


class Canvas:
    def __init__(self):
        self.side = SIZE * SCALE
        self.pixels = bytearray(self.side * self.side)
        self.abrasion = bytearray(SIZE * SIZE)
        self.pen = Random(PRINT_SEED + 9)

    def span(self, x0, x1, y, color):
        if 0 <= y < self.side:
            x0, x1 = max(0, x0), min(self.side, x1)
            if x1 > x0:
                start = y * self.side + x0
                self.pixels[start:start + x1 - x0] = bytes((color,)) * (x1 - x0)

    def polygon(self, points, color):
        points = [(x * SCALE, y * SCALE) for x, y in points]
        edges = tuple(zip(points[-1:] + points[:-1], points))
        for row in range(max(0, math.floor(min(y for x, y in points))),
                         min(self.side, math.ceil(max(y for x, y in points)))):
            scan = row + 0.5
            intersections = sorted(
                x0 + (scan - y0) * (x1 - x0) / (y1 - y0)
                for (x0, y0), (x1, y1) in edges if min(y0, y1) <= scan < max(y0, y1)
            )
            for x0, x1 in zip(intersections[::2], intersections[1::2]):
                self.span(math.ceil(x0 - .5), math.ceil(x1 - .5), row, color)

    def circle(self, x, y, radius, color):
        x, y, radius = x * SCALE, y * SCALE, radius * SCALE
        for row in range(math.floor(y - radius), math.ceil(y + radius)):
            vertical = row + .5 - y
            if abs(vertical) < radius:
                half = math.sqrt(radius * radius - vertical * vertical)
                self.span(math.ceil(x - half - .5), math.ceil(x + half - .5), row, color)

    def line(self, x0, y0, x1, y1, color, width=1):
        length = math.hypot(x1 - x0, y1 - y0)
        if length == 0:
            return
        dx = (y1 - y0) * width / (2 * length)
        dy = (x0 - x1) * width / (2 * length)
        self.polygon(((x0 + dx, y0 + dy), (x1 + dx, y1 + dy),
                      (x1 - dx, y1 - dy), (x0 - dx, y0 - dy)), color)

    def text(self, x, baseline, text, font, color=INK, *, align="left",
             tracking=0, scale=1, squeeze=1, distress=False):
        inset = {"left": 0, "center": .5, "right": 1}[align]
        horizontal = scale * squeeze
        pen = round((x - inset * text_width(text, font, tracking, scale, squeeze)) * SCALE)
        baseline = round(baseline * SCALE)
        letter_gap = round(tracking * SCALE)
        if distress:
            cap = max(-glyph(font, c)[2] for c in text)
            left = max(0, pen // SCALE - 2)
            right = min(SIZE, left + math.ceil(text_width(text, font, tracking, scale, squeeze)) + 5)
            top = max(0, (baseline - round(cap * scale)) // SCALE - 2)
            bottom = min(SIZE, baseline // SCALE + 15)
            abrade_ink(self.abrasion, left, top, right, bottom,
                       print_mark(pen, baseline), font != "display27")
        for index, character in enumerate(text):
            advance, left, top, width, height, bitmap = glyph(font, character)
            stride = (width + 7) // 8
            x0, y0 = pen + round(left * horizontal), baseline + round(top * scale)
            x1, y1 = x0 + round(width * horizontal), y0 + round(height * scale)
            left_edge, right_edge = max(0, x0), min(x1, self.side)
            impression = print_mark(pen + index * 29, baseline + ord(character))
            pigment = color
            if color == INK:
                pigment = DISPLAY_INK + impression % 5 if distress else BODY_INK + impression % 3
            bleed_x = 2 if impression & 8 else -2
            bleed_y = 2 + (impression & 1)
            for y in range(max(0, y0), min(y1, self.side)):
                source_row = min(height - 1, int((y - y0) / scale)) * stride
                target_row = y * self.side
                for x in range(left_edge, right_edge):
                    col = min(width - 1, int((x - x0) / horizontal))
                    if bitmap[source_row + col // 8] & (0x80 >> (col % 8)):
                        self.pixels[target_row + x] = pigment
                        # Pressed ink creeps unevenly along short runs of the edge.
                        if distress and (x // 4 + y // 5 + impression) % 13 < 8:
                            bx, by = x + bleed_x, y + bleed_y
                            if 0 <= bx < self.side and by < self.side:
                                offset = by * self.side + bx
                                if self.pixels[offset] == PAPER:
                                    self.pixels[offset] = BLEED_INK
            pen += round(advance * horizontal) + letter_gap

    def png(self):
        # The packed channels each have ample room for the sum of nine samples.
        # This integer box filter creates no platform-dependent color profiles.
        def packed(rgb):
            red, green, blue = rgb
            return (red << 24) | (green << 12) | blue

        weights = tuple(map(packed, PALETTE))
        paper = paper_colors()
        paper_weights = {shade: packed(rgb) for shade, rgb in paper.items()}
        wear = print_field(Random(PRINT_SEED + 4), 11, 18)
        scanlines = bytearray()
        side = self.side
        for y, (paper_row, wear_row) in enumerate(zip(Newsprint().rows(), wear)):
            start = y * SCALE * side
            rows = (self.pixels[start:start + side],
                    self.pixels[start + side:start + 2 * side],
                    self.pixels[start + 2 * side:start + 3 * side])
            line = bytearray()
            for x, (shade, mark) in enumerate(paper_row):
                i = x * SCALE
                a, b, c = (row[i:i + SCALE] for row in rows)
                uncovered = a.count(PAPER) + b.count(PAPER) + c.count(PAPER)
                ground = paper[shade]
                if uncovered == 9:
                    line.extend(ground)
                    continue
                raised = (mark >> 27) & 31
                texture = wear_row[x]
                tint = (9 - uncovered) * ((texture + raised - 16) // 10)
                mix = sum(weights[index] for row in (a, b, c) for index in row if index)
                mix += paper_weights[shade] * uncovered
                value = (((mix >> 24) + tint + 4) // 9,
                         (((mix >> 12) & 4095) + tint + 4) // 9,
                         ((mix & 4095) + tint + 4) // 9)
                loss = self.abrasion[y * SIZE + x]
                fine_loss = max(0, raised + texture // 3 - 24) * 3
                if (loss or fine_loss) and any(DISPLAY_INK <= index <= BLEED_INK
                                               for row in (a, b, c) for index in row):
                    # Full losses reveal the sheet. Partial losses leave residual ink.
                    value = mix_color(value, ground, max(loss, fine_loss))
                line.extend(value)
            # PNG Sub prediction keeps the grain inexpensive to encode.
            scanlines.append(1)
            scanlines.extend(line[:3])
            scanlines.extend((b - a) & 255 for a, b in zip(line, line[3:]))

        def chunk(kind, data):
            return (struct.pack(">I", len(data)) + kind + data +
                    struct.pack(">I", zlib.crc32(kind + data)))

        header = struct.pack(">IIBBBBB", SIZE, SIZE, 8, 2, 0, 0, 0)
        return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) +
                chunk(b"IDAT", zlib.compress(scanlines, 9)) + chunk(b"IEND", b""))


def cut_line(page, first, last, ink, width, *, overprint=False):
    x, y = first
    dx, dy = last[0] - x, last[1] - y
    length = math.hypot(dx, dy)
    if length == 0:
        return
    nx, ny = -dy / length, dx / length
    pieces = max(1, math.ceil(length / (9 if overprint else 11)))
    random = page.pen
    points = [first]
    drift = 0
    for step in range(1, pieces):
        fraction = step / pieces
        drift = .63 * drift + random.uniform(-.79, .79) if overprint else (
            .54 * drift + random.uniform(-.56, .56))
        points.append((x + dx * fraction + drift * nx, y + dy * fraction + drift * ny))
    points.append(last)
    if overprint:
        # The second impression slips to one side and catches only in patches.
        for (ax, ay), (bx, by) in zip(points, points[1:]):
            if random.random() < .67:
                offset = random.uniform(.43, 1.40)
                page.line(ax + nx * offset, ay + ny * offset,
                          bx + nx * offset, by + ny * offset, FAINT_INK, width * .43)
    for (ax, ay), (bx, by) in zip(points, points[1:]):
        pressure = random.uniform(.69, 1.25) if overprint or pieces > 1 else 1
        pigment = HALF_INK if overprint and ink == INK and random.random() < .08 else ink
        page.line(ax, ay, bx, by, pigment, width * pressure)


def stroke(page, points, color=INK, width=1, *, close=False):
    following = (*points[1:], points[0]) if close else points[1:]
    for a, b in zip(points, following):
        cut_line(page, a, b, color, width)


def hatch(page, points, *, spacing=4, slope=.55, ink=HALF_INK, width=.65):
    """Cut uneven burin strokes clipped to the edges of a drawn shape."""
    random = page.pen
    edges = tuple(zip(points, (*points[1:], points[0])))
    pivot = sum(x for x, y in points) / len(points)
    bounds = [y - slope * (x - pivot) for x, y in points]
    spread = .14 * max(abs(x - pivot) for x, y in points)
    first = math.floor((min(bounds) - spread) / spacing)
    last = math.ceil((max(bounds) + spread) / spacing)

    for index in range(first, last):
        level = (index + random.uniform(-.47, .47)) * spacing
        direction = slope + random.uniform(-.14, .14)
        cuts = []
        for (ax, ay), (bx, by) in edges:
            near, far = ay - direction * (ax - pivot), by - direction * (bx - pivot)
            if min(near, far) <= level < max(near, far):
                cuts.append(ax + (bx - ax) * (level - near) / (far - near))
        cuts.sort()
        for start, end in zip(cuts[::2], cuts[1::2]):
            if end - start > 1.5:
                weight = width * random.uniform(.36, 1.86)
                start += min((end - start) * .15, random.uniform(0, 1.5))
                end -= min((end - start) * .15, random.uniform(0, 1.5))
                cut_line(page, (start, level + direction * (start - pivot)),
                         (end, level + direction * (end - pivot)), ink, weight)


class Drawing:
    """Local coordinates for the small news illustrations."""

    def __init__(self, page, x, y):
        self.page, self.x, self.y = page, x, y

    def line(self, *points, ink=INK, width=1.15, close=False):
        stroke(self.page, [(self.x + x, self.y + y) for x, y in points],
               ink, width, close=close)

    def arc(self, cx, cy, rx, ry, start, stop, ink=INK, width=1):
        steps = max(8, round(abs(stop - start) * max(rx, ry) / 260))
        angles = (math.radians(start + (stop - start) * i / steps)
                  for i in range(steps + 1))
        points = [(cx + rx * math.cos(a), cy + ry * math.sin(a)) for a in angles]
        self.line(*points, ink=ink, width=width)

    def dot(self, x, y, size, ink=INK):
        self.page.circle(self.x + x, self.y + y, size, ink)

    def paper(self, *points):
        self.page.polygon([(self.x + x, self.y + y) for x, y in points], PAPER)

    def hatch(self, *points, **options):
        hatch(self.page, [(self.x + x, self.y + y) for x, y in points], **options)

    def text(self, x, y, label, font, ink=INK, **options):
        self.page.text(self.x + x, self.y + y, label, font, ink, **options)


def typeset(page, x, y, lines, font, width, leading, *, ink=INK, scale=1, squeeze=1,
            distress=False):
    for line in lines:
        assert text_width(line, font, scale=scale, squeeze=squeeze) <= width, line
        page.text(x, y, line, font, ink, scale=scale, squeeze=squeeze, distress=distress)
        y += leading
    return y


def paragraph(page, x, y, copy, width, *, font="news14", leading=17, limit=3):
    lines = wrap(copy, font, width)
    assert len(lines) <= limit, copy
    return typeset(page, x, y, lines, font, width, leading)


def rule(page, y, x=32, width=960, ink=RULE, weight=1):
    center = y + weight / 2
    cut_line(page, (x, center), (x + width, center), ink, weight, overprint=True)


def column_rule(page, x, top, bottom, ink=RULE, weight=.65):
    center = x + weight / 2
    cut_line(page, (center, top), (center, bottom), ink, weight, overprint=True)


def double_rule(page, y):
    rule(page, y, ink=INK, weight=1.65)
    rule(page, y + 3.4, ink=INK, weight=.67)


def masthead(page):
    page.text(32, 19, "The World in Brief", "display22", scale=.66)
    page.text(992, 19, "21 Reports, UTC Edition", "display22", align="right", scale=.66)
    date = "Saturday, 21 November 2026"
    page.text(512, 89, date, "display55", align="center", scale=1.32, squeeze=.88, distress=True)
    double_rule(page, 114)


def tanker(d):
    # The waterline and the low open deck distinguish a tanker from a container ship.
    hull = ((9, 89), (56, 96), (353, 95), (415, 81), (396, 105),
            (368, 123), (56, 128), (31, 118))
    d.hatch(*hull, spacing=2.8, slope=-.83, ink=INK, width=.94)
    d.line(*hull, close=True, width=2.2)
    d.line((24, 107), (62, 118), (365, 116), (394, 101), width=1.25)
    bridge = ((42, 94), (42, 56), (31, 54), (31, 46), (84, 45),
              (88, 53), (82, 55), (82, 94))
    d.hatch(*bridge, spacing=4, slope=.5, ink=HALF_INK)
    d.line(*bridge, close=True, width=1.65)
    for x in range(37, 80, 8):
        d.line((x, 49), (x+4, 49), width=2)
    d.line((56, 45), (56, 26), (59, 25), (59, 45), width=1)
    d.line((49, 34), (67, 34), width=1.25)
    for x in range(104, 348, 35):
        d.line((x, 92), (x, 84), (x+15, 83), (x+18, 91), width=1.5)
        d.line((x+2, 80), (x+12, 80), width=1)
    d.line((94, 88), (351, 87), (376, 82), width=1.2)
    d.line((371, 89), (371, 59), (378, 57), width=1.35)
    for row in range(5):
        for band in range(7):
            x = 4 + band * 60 + (row % 2) * 8
            y = 133 + row * 5 + math.sin(band + row) * 2
            d.line((x, y), (x+14, y-2), (x+29, y+1), (x+46, y-2),
                   ink=HALF_INK if row < 2 else RULE, width=.72)
    d.text(4, 173, "OIL TRAFFIC  /  STRAIT OF HORMUZ", "news12")


def critical_line(d):
    # A schematic complex plane: the first three nontrivial zeros above the real axis.
    left, right, middle = 37, 175, 106
    top, bottom = 20, 147
    d.hatch((left, top), (right, top), (right, bottom), (left, bottom),
            spacing=9, slope=-1.2, ink=FAINT_INK, width=.6)
    d.line((left, top), (left, bottom), (right+18, bottom), ink=INK, width=1.45)
    d.line((right, top), (right, bottom), ink=RULE)
    d.line((middle, top), (middle, bottom), width=2)
    for ordinate, label in ((14.13, "14.13"), (21.02, "21.02"), (25.01, "25.01")):
        y = bottom - ordinate * 4.5
        d.dot(middle, y, 3.6)
        d.text(middle+11, y+4, label, "news12")
    d.text(left, 163, "0", "news12", align="center")
    d.text(middle, 163, "1/2", "news12", align="center")
    d.text(right, 163, "1", "news12", align="center")
    d.text(110, 10, "THE CRITICAL LINE", "news12", align="center")
    d.text(110, 182, "Real part of a zeta zero", "news12", align="center")


def conference(d):
    # A line drawing of a negotiation table, with an edited draft in the foreground.
    d.hatch((23, 113), (59, 115), (221, 114), (215, 136), (183, 157),
            (73, 169), (45, 157), spacing=3.70, slope=.27, ink=FAINT_INK)
    d.hatch((37, 75), (178, 75), (218, 107), (60, 107),
            spacing=3.2, slope=.13, ink=RULE, width=.62)
    d.hatch((37, 75), (60, 107), (218, 107), (219, 114), (60, 114),
            (37, 81), spacing=2.65, slope=1.39, ink=INK, width=.75)
    d.line((37, 75), (178, 75), (218, 107), (60, 107), close=True, width=1.55)
    d.line((60, 107), (60, 114), (219, 114), (218, 107), width=1.3)
    d.line((37, 75), (37, 81), (60, 114), width=1.2)
    for x, y in ((48, 45), (88, 45), (128, 45), (168, 45)):
        d.hatch((x - 12, y), (x - 9, y - 7), (x - 5, y - 9),
                (x - 1, y - 9), (x + 4, y + 11), (x - 12, y + 13),
                spacing=2.2, slope=.65, width=.65)
        d.arc(x, y, 12, 10, 180, 360, INK, 1.38)
        d.arc(x, y + 2, 9.5, 9.5, 205, 336, HALF_INK, .78)
        d.line((x - 12, y), (x - 12, y + 13), (x + 12, y + 13), (x + 12, y), width=1.25)
        d.line((x + 2, 76), (x + 2, 70), (x + 6, 65), width=1.25)
        d.line((x - 8, 82), (x + 7, 83), ink=INK, width=.85)
        d.dot(x + 6, 65, 1.3)
    draft = ((74, 93), (163, 93), (190, 166), (83, 166))
    d.paper(*draft)
    d.hatch((75, 94), (85, 95), (92, 159), (174, 160), (187, 166),
            (83, 166), spacing=3, slope=-.64, ink=RULE, width=.62)
    d.line(*draft, close=True, width=1.45)
    d.line((83, 169), (194, 169), (166, 96), ink=HALF_INK, width=.9)
    for y, end in ((112, 151), (117, 166), (125, 159), (133, 173),
                   (140, 166), (147, 171), (153, 177)):
        d.line((89 + (y - 108) / 10, y), (end, y), ink=HALF_INK, width=.75)
    d.line((89, 131), (173, 135), ink=INK, width=1.5)
    d.line((110, 104), (139, 104), ink=INK, width=1.1)
    d.line((175, 151), (202, 118), (206, 121), (179, 154), (173, 157),
           (175, 151), ink=INK, width=1.05)
    d.line((177, 152), (204, 120), ink=HALF_INK, width=.75)


def lead_stories(page):
    column_rule(page, 468, 124, 458, HALF_INK, .85)
    column_rule(page, 736, 124, 458, HALF_INK, .85)
    typeset(page, 32, 176, ("THREE TANKERS", "HIT NEAR HORMUZ"),
            "display55", 422, 47, scale=.94, squeeze=.74, distress=True)
    paragraph(page, 32, 249, "Projectiles hit two tankers leaving the Gulf. Iran says a third ship struck a mine east of the strait.", 423, limit=2)
    page.text(32, 283, "Shipping reports  /  AP", "news12")
    tanker(Drawing(page, 32, 283))

    conference(Drawing(page, 479, 130))
    typeset(page, 488, 345, ("COP31 SPLITS", "ON FOSSIL FUELS"),
            "display27", 235, 29, scale=1.01, squeeze=.84, distress=True)
    paragraph(page, 488, 398, "The EU and Pacific islands press for fossil fuel cuts. African negotiators seek more money for adaptation.", 226, leading=15, limit=4)
    page.text(488, 457, "Antalya  /  BBC", "news12")

    critical_line(Drawing(page, 765, 130))
    typeset(page, 752, 345, ("RIEMANN PROOF", "PASSES CHECKS"),
            "display27", 240, 29, scale=1.01, squeeze=.86, distress=True)
    paragraph(page, 752, 398, "Independent tools verify the Lean proof of a conjecture about prime numbers first posed in 1859.", 237, leading=15, limit=4)
    page.text(752, 458, "Lean community  /  Mathlib", "news12")


DESK_COLUMNS = (
    (32, 293, "display27", (
        (497, ("Missile hits", "Kryvyi Rih"), ("Two killed and 60 wounded", "in the Ukrainian city.")),
        (600, ("Mexico captures", "El Chapo Isidro"), ("11 die in violence in Sinaloa.",)),
    )),
    (349, 294, "display22", (
        (497, ("Geneva arms talks stall",), ("Nations fail to set treaty talks", "on autonomous weapons.")),
        (567, ("Gaza food truck hit",), ("Three men killed in Israeli strike.",)),
        (632, ("Fire in Bahrain",), ("Ministry reports an Iranian strike", "on a civilian industrial site.")),
    )),
    (668, 324, "display22", (
        (497, ("Cargo ship burns in Baltic",), ("Sparta II drifts into Finnish waters.",)),
        (555, ("300 return by trawler",), ("After Cyclone Akvan, about 1,200", "remain on a Bangladeshi island.")),
        (635, ("Basra power plant fire",), ("At least four dead and 35 injured.",)),
    )),
)


def news_desk(page):
    double_rule(page, 466)
    page.text(32, 489, "The News Desk", "display22", scale=.78)
    for x in (337, 655):
        column_rule(page, x, 498, 691)
    for x, width, font, stories in DESK_COLUMNS:
        heading_step = 29 if font == "display27" else 23
        for top, heading, copy in stories:
            rule(page, top, x, width, weight=.65)
            end = typeset(page, x, top + heading_step + 1, heading, font, width,
                          heading_step, scale=1.04)
            typeset(page, x, end - heading_step + 21, copy, "news14", width,
                    18, scale=1.15)


MARKETS = (
    ("S&P 500", "6,910.39"),
    ("Brent", "$92.57"),
    ("Bitcoin", "$58,110.53"),
    ("Ether", "$1,649.83"),
)


def markets(page):
    double_rule(page, 707)
    page.text(32, 724, "Markets  /  Friday closes    ·    Crypto  /  Saturday noon UTC", "display22", scale=.64)
    rule(page, 720, x=440, width=552, weight=.65)
    x = 32
    for i, (symbol, value) in enumerate(MARKETS):
        if i:
            page.text(x + 7, 746, "·", "display22")
            x += 22
        page.text(x, 747, symbol, "news14", scale=1.12)
        x += text_width(symbol, "news14", scale=1.12) + 7
        page.text(x, 748, value, "display27", scale=1.14)
        x += text_width(value, "display27", scale=1.14)
    assert x <= 992
    rule(page, 755, ink=INK, weight=1.2)


BRIEFS = (
    ("Magnitude 6.8 near Timor-Leste", "USGS locates the quake northeast of Lospalos."),
    ("Aoun urges Israeli withdrawal", "He also urges Hezbollah to give up its arms."),
    ("Rutte backs Poland in Warsaw", "NATO chief condemns Friday’s airspace breach."),
    ("FBI investigates possible database breach", "Reports point to the national crime database."),
    ("India’s Congress youth wing releases video", "Footage shows Friday’s protests at Meta offices."),
    ("Magnitude 6.7 in Peru’s Andes", "The quake struck at 7:09 p.m. Friday local time."),
    ("African football backs Infantino", "CAF chief says all 54 members back his bid."),
    ("Ukraine defends Crimea bridge strikes", "Zelensky calls the strikes a response to attacks."),
    ("Australia wins T20 opener", "England beaten by three wickets in Melbourne."),
    ("Alcaraz reaches Turin final", "He beats Ben Shelton in a third-set tiebreak."),
)


def news_briefs(page):
    page.text(512, 771, "In Brief", "display22", scale=.82, align="center")
    rule(page, 766, width=430, weight=.65)
    rule(page, 766, x=562, width=430, weight=.65)
    column_rule(page, 512, 782, 967)
    for i, (heading, copy) in enumerate(BRIEFS):
        column, row = divmod(i, 5)
        x, y = 32 + column * 498, 796 + row * 40
        typeset(page, x, y, (heading,), "display22", 462, 0, scale=.96)
        typeset(page, x, y + 18, (copy,), "news14", 462, 0, scale=1.22)


def footer(page):
    double_rule(page, 980)
    page.text(32, 999, "DATE CHECK", "display22", scale=.73)
    typeset(page, 147, 999, (
        "21 November in UTC. Peru’s quake and the Sinaloa arrest fell on Friday evening locally. Edition closed at 20:40 UTC.",
    ), "news12", 845, 0, scale=1.05)
    typeset(page, 32, 1015, (
        "Reporting: AP, BBC, Reuters, Al Jazeera, The Guardian and Prothom Alo. Data: USGS, Lean community and Coinbase Exchange.",
    ), "news12", 960, 0, squeeze=.91)


def main():
    page = Canvas()
    masthead(page)
    lead_stories(page)
    news_desk(page)
    markets(page)
    news_briefs(page)
    footer(page)
    output = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    output.mkdir(parents=True, exist_ok=True)
    (output / "entry.png").write_bytes(page.png())


if __name__ == "__main__":
    main()
