#!/usr/bin/perl

use strict;
use lib "/project/devtools/perl/lib";
use lib "/project/devtools/perl/lib/lib64/perl5";

use Getopt::Long;
use Pod::Usage;
use Log::Log4perl;
use Log::Log4perl::Level;
use IPC::Open3;

our $Ct="/usr/atria/bin/cleartool";
our $CtCom;
our $Record;
our $Vob;
our %VHash; 
our $Action="list";
our $AccessDate;
our $Result;
our $Help; 
our $HostName; 
our $LogFile;
our $Man;
our $Owner;
our $LogPriority;
our $Uuid;
our $ViewTag;
our $ViewType;
our $HasErrors;


$Result = GetOptions
    (
       "a|action=s"     => \$Action,
       "d|accessDate=s" => \$AccessDate,
       "h|host=s"       => \$HostName,
       "help|?"         => \$Help,
       "l|logfile=s"    => \$LogFile,
       "man"            => \$Man,
       "o|owner=s"      => \$Owner,
       "uuid=s"         => \$Uuid,
       "t|v|tag|view=s" => \$ViewTag,
       "type=s"         => \$ViewType,
       "verbosity=s"    => \$LogPriority
    );

sub logfile
{
    if( exists $Result->{logfile} ) 
    {
        return $Result->{logFile};
    } 
    else 
    {
        return "test.log";
    }     
}

sub init
{

    my $rval=1; 
    my $logMsg;

    Log::Log4perl::init_and_watch('viewsByHost.conf', 10);
    my $logger = Log::Log4perl->get_logger('viewsByHost.init');

    if( $LogPriority )
    {
        $logger->level($LogPriority); # one of DEBUG, INFO, WARN, ERROR, FATAL
    }

    if( $Help )
    {
        pod2usage(1);
        $rval=0;
    }

    if( $Man )
    {
        pod2usage(-exitstatus => 0, -verbosity => 2);
        $rval=0;
    }

    if( $rval )
    {

        $CtCom="$Ct lsview -l -properties -full"; 
        $HasErrors=0;

        if( $HostName )
        { 
            $CtCom .= " -host $HostName"; 
        }

        if( $ViewTag && $Uuid )
        {
            $logMsg="Can't specify -uuid with either -tag or -view.";
            $logger->error($logMsg);
            $rval=0;
        }
        else
        {

            if( $Uuid )
            { 
                $CtCom .= " -uuid $Uuid"; 
            }

            if( $ViewTag )
            { 
                $CtCom .= " $ViewTag"; 
            }
        }

    }

    if ( $rval )
    {
        # Validations for options that may be
        # used to pare-down the view hash after
        # it has been loaded from the lsview command 

        if( $AccessDate )
        {
            if( $AccessDate =~ /\d{4}-\d\d-\d\d/ )
            {
            }
            else
            {
                $logMsg="Must specify access date in YYYY-MM-DD format.";
                $logger->error($logMsg);
                $rval=0;
            }
        }

        if( $ViewType )
        {
            if( $ViewType =~ /(dynamic|snapshot)/i )
            {
            }
            else
            {
                $logMsg="View type (-type) must be either";
                $logMsg.="'snapshot' or 'dynamic'.";
                $logger->error($logMsg);
                $rval=0;
            }
        }

    }

    if ( $rval )
    {

        $logger->debug("Running command: $CtCom");
    }

    return $rval;

}

sub loadViewHash
{

    my $rval=1; 
    my $logger = Log::Log4perl->get_logger('viewsByHost.loadViewArray');
    my $result;
    my $viewTag;
    my $lineParsed; 
    my $vHashRef=$_[0];
    my $hasErrors=0;

    my $ctPid;

    if( $LogPriority )
    {
        $logger->level($LogPriority); 
    }

    $ctPid = open3(\*WRITER, \*READER, \*ERROR, $CtCom);

    $logger->debug("\$ctPid=$ctPid");

    if( $ctPid )
    {
        $viewTag="";

        #while( my $errout = <ERROR> ) 
        #{
        #    #print "err->$errout";
        #    $hasErrors=1; 
        #}

        while ( $result = <READER> )
        {

            #Tag: ravi_sun8
            #  Global path: /var/scm/ASview01/airflite/ravit/ravi_sun8.vws
            #  Server host: cmeuxdfw02
            #  Region: sdt
            #  Active: NO
            #  View tag uuid:6daa6325.534d11d8.8ee3.00:01:80:b6:6c:e9
            #View on host: cmeuxdfw02
            #View server access path: /var/scm/ASview01/airflite/ravit/ravi_sun8.vws
            #View uuid: 6daa6325.534d11d8.8ee3.00:01:80:b6:6c:e9
            #View owner: dev.sabre.com/ravit
            #
            #Created 2004-01-30T11:47:55-06:00 by ravit.slotgrp@pigpen
            #Last modified 2010-05-26T08:36:23-05:00 by ravit.slotgrp@solaris8p
            #Last accessed 2010-06-17T08:13:40-05:00 by ravit.slotgrp@solaris8p
            #Last read of private data 2010-06-17T08:13:40-05:00 by ravit.slotgrp@solaris8p
            #Last derived object promotion 2008-05-08T17:26:25-05:00 by ravit.slotgrp@mustang-450
            #Last config spec update 2007-03-23T16:41:52-05:00 by ravit.slotgrp@mustang-450
            #Last derived object winkin 2008-05-21T17:33:52-05:00 by ravit.slotgrp@mustang-450
            #Last derived object creation 2008-05-21T17:34:22-05:00 by ravit.slotgrp@mustang-450
            #Last view private object update 2010-05-26T08:36:23-05:00 by ravit.slotgrp@solaris8p
            #Text mode: unix
            #Properties: dynamic readwrite shareable_dos
            #Owner: dev.sabre.com/ravit : rwx (all)
            #Group: dev.sabre.com/slotgrp : rwx (all)
            #Other:                  : r-x (read)

            $lineParsed=0; 
            if( $result =~ /^Tag:\s+(.*)$/ )
            {
                $logger->debug("Parsing data for view tag: $1"); 
                $viewTag=$1; 
                $lineParsed=1; 
            }
            else
            {
                if( $viewTag )
                {
                    if( !$lineParsed )
                    {
                        if( $result =~ /^\s*Global path:\s+(.*)$/ )
                        {
                            #$logger->debug("Adding globalPath"); 
                            $vHashRef->{$viewTag}{globalPath}=$1;
                            $lineParsed=1; 
                        }
                    }

                    if( !$lineParsed )
                    {
                        if( $result =~ /^\s*Server host:\s+(.*)$/ )
                        {
                            $vHashRef->{$viewTag}{serverHost}=$1;
                            $lineParsed=1; 
                        }
                    }

                    if( !$lineParsed )
                    {
                        if( $result =~ /^\s*Active:\s+(.*)$/ )
                        {
                            $vHashRef->{$viewTag}{active}=$1;
                            $lineParsed=1; 
                        }
                    }

                    if( !$lineParsed )
                    {
                        if( $result =~ /^\s*View uuid:\s+(.*)$/ )
                        {
                            $vHashRef->{$viewTag}{viewUuid}=$1;
                            $lineParsed=1; 
                        }
                    }

                    if( !$lineParsed )
                    {
                        if( $result =~ /^\s*View on host:\s+(.*)$/ )
                        {
                            $vHashRef->{$viewTag}{viewHost}=$1;
                            $lineParsed=1; 
                        }
                    }

                    if( !$lineParsed )
                    {
                        #dev.sabre.com/
                        if( $result =~ /^\s*View owner:\s+((?:dev\.sabre\.com\/)?(.*))$/ )
                        {
                            $vHashRef->{$viewTag}{viewOwner}=$1;
                            $vHashRef->{$viewTag}{viewOwnerId}=$2;
                            $lineParsed=1; 
                        }
                    }

                    if( !$lineParsed )
                    {
                        if( $result =~ /^Created\s+([^ ]+)\s+by\s+(.*)$/ )
                        {
                            $vHashRef->{$viewTag}{createdDate}=$1;
                            $vHashRef->{$viewTag}{createdUser}=$2;
                            $lineParsed=1; 
                        }
                    }

                    if( !$lineParsed )
                    {
                        if( $result =~ /^Last modified\s+([^ ]+)\s+by\s+(.*)$/ )
                        {
                            $vHashRef->{$viewTag}{lastModifiedDate}=$1;
                            $vHashRef->{$viewTag}{lastModifiedUser}=$2;
                            $lineParsed=1; 
                        }
                    }

                    if( !$lineParsed )
                    {
                        if( $result =~ /^Last accessed\s+([^ ]+)\s+by\s+(.*)$/ )
                        {
                            $vHashRef->{$viewTag}{lastAccessedDate}=$1;
                            $vHashRef->{$viewTag}{lastAccessedUser}=$2;
                            $lineParsed=1; 
                        }
                    }

                    if( !$lineParsed )
                    {
                        if( $result =~ /^Last read of private data\s+([^ ]+)\s+by\s+(.*)$/ )
                        {
                            $vHashRef->{$viewTag}{lastReadOfPrivateDataDate}=$1;
                            $vHashRef->{$viewTag}{lastReadOfPrivateDataUser}=$2;
                            $lineParsed=1; 
                        }
                    }

                    if( !$lineParsed )
                    {
                        if( $result =~ /^Last config spec update\s+([^ ]+)\s+by\s+(.*)$/ )
                        {
                            $vHashRef->{$viewTag}{lastConfigSpecUpdateDate}=$1;
                            $vHashRef->{$viewTag}{lastConfigSpecUpdateUser}=$2;
                            $lineParsed=1; 
                        }
                    }

                    if( !$lineParsed )
                    {
                        if( $result =~ /^Last view private object update\s+([^ ]+)\s+by\s+(.*)$/ )
                        {
                            $vHashRef->{$viewTag}{lastViewPrivateObjectUpdateDate}=$1;
                            $vHashRef->{$viewTag}{lastViewPrivateObjectUpdateUser}=$2;
                            $lineParsed=1; 
                        }
                    }

                    if( !$lineParsed )
                    {
                        if( $result =~ /^Properties:\s+(.*)$/ )
                        {
                            
                            $vHashRef->{$viewTag}{properties}=[ split / /, $1 ];
                            $lineParsed=1; 
                        }
                    }

                    if( !$lineParsed )
                    {
                        if( $result =~ /^\s*Owner:\s+([^ ]+)\s+:\s+([^ ]+)\s+\((.*)\)$/ )
                        {
                            $vHashRef->{$viewTag}{owner}=$1;
                            $vHashRef->{$viewTag}{ownerPermissions}=$2;
                            $vHashRef->{$viewTag}{ownerPermissionsScope}=$3;
                            $lineParsed=1; 
                        }
                    }

                    if( !$lineParsed )
                    {
                        if( $result =~ /^\s*Group:\s+([^ ]+)\s+:\s+([^ ]+)\s+\((.*)\)$/ )
                        {
                            $vHashRef->{$viewTag}{group}=$1;
                            $vHashRef->{$viewTag}{groupPermissions}=$2;
                            $vHashRef->{$viewTag}{groupPermissionsScope}=$3;
                            $lineParsed=1; 
                        }
                    }

                }
                else
                {
                    $logger->debug("Not within a view so skipping this line: $result"); 
                }
            }
        }


    }
    else
    {
        $logger->error("Can't run '$CtCom' due to $!"); 
        $rval=0;
    }

    if ( waitpid( $ctPid, 0 ) )
    {}
    else
    {
        $logger->error("Unable to reap the command due to $!");
        $rval=0;
    }

    return $rval;

}

sub meetsDate
{

    my $rval=1;
    my $viewTag=$_[0]; # just passing for troubleshooting views
    my $testDateArg=$_[1];
    my $baseDateArg=$_[2];

    my $testDate;
    my $baseDate;
    my $logMsg;

    my $logger = Log::Log4perl->get_logger('viewsByHost.meetsDate');
    if( $LogPriority )
    {
        $logger->level($LogPriority);
    }
    
    if( $rval )
    {
        if( $testDateArg =~ /^(\d{4}-\d\d-\d\d).*/ )
        {
            $testDate="$1";
        }
        else
        {
            $logMsg="For $viewTag, can't parse test date from $testDateArg";
            $logger->error($logMsg); 
            $rval=0;
        } 
    }
        
    if( $rval )
    {
        if( $baseDateArg =~ /^(\d{4}-\d\d-\d\d).*/ )
        {
            $baseDate="$1";
        }
        else
        {
            $logMsg="for $viewTag, can't parse base date from $baseDateArg";
            $logger->error($logMsg); 
            $rval=0;
        } 
    }
        

    if( $rval )
    {
        if( $testDate ge $baseDate )
        {  
            #$logger->debug("$testDate meets the date: $baseDate"); 
        }
        else
        {
            #$logger->debug("$testDate doesn't meet the date: $baseDate"); 
            $rval=0;
        }
    }

    return $rval;

}

sub listViews
{

    my $listFormat=$_[0];
    my $vHashRef=$_[1];
    my $viewTag;
    my $viewKey;
    my $propNdx;
    my $numProps;
    my $logMsg;
    my $include;
    my $propValue;
    my %includeHash;

    my $logger = Log::Log4perl->get_logger('viewsByHost.listViews');
    if( $LogPriority )
    {
        $logger->level($LogPriority);
    }

    for $viewTag (sort keys %{ $vHashRef } )
    {    

        $include=1; 

        # filter through the hash
        if( $AccessDate )
        {
            $include=0; 
            if( meetsDate( 
                $viewTag,
                $vHashRef->{$viewTag}{lastAccessedDate}, 
                $AccessDate ) 
              )
            {
                $include=1; 
            }
        }

        if( $include && $Owner )
        {
            $include=$vHashRef->{$viewTag}{viewOwnerId} =~ /.*$Owner.*/;
        }

        if( $include && $ViewType )
        {
        
            # don't know which property will have the
            # view type so have to iterate through all  
            $include = 0;
            $numProps=scalar @{ 
                $vHashRef->{$viewTag}{properties} };
            for ( $propNdx = 0 ; 
                  $propNdx < $numProps; 
                  $propNdx += 1 ) 
            {
                $propValue=$vHashRef->{$viewTag}
                    {properties}[$propNdx];

                if( $propValue =~ /$ViewType/ )
                {
                    $logMsg = "View matches specified view type"; 
                    $logger->debug($logMsg); 
                    $include=1;
                    last;
                }
            } # for
        }

        if( $include )
        {    

            if( $listFormat =~ /short/i  )
            {
                $logger->info("$viewTag");
            }
            else
            {

                $logger->info("View record for $viewTag");
                for $viewKey (sort keys %{ $vHashRef->{$viewTag} } )
                {    
                    if( $viewKey =~ /^properties$/ )
                    {
                        $numProps=scalar @{ 
                            $vHashRef->{$viewTag}{properties} };

                        #$logger->debug("  # of props: $numProps"); 

                        for ( $propNdx = 0 ; $propNdx < $numProps ; $propNdx += 1 )
                        {
                            $logMsg = "  $viewKey ($propNdx): "; 
                            $logMsg .= $vHashRef->{$viewTag}{$viewKey}[$propNdx];
                            $logger->info($logMsg); 
                        }
                    }
                    else
                    {
                        $logMsg = "  $viewKey: ";
                        $logMsg .= $vHashRef->{$viewTag}{$viewKey}; 
                        $logger->info($logMsg); 
                    }
                }
            } # $listFormat =~ /short/i

        } # include
    }

}

if( init )
{
    
    if( loadViewHash(\%VHash) )
    {
        listViews($Action, \%VHash);
    }

}
else
{
}

__END__

=head1 NAME

viewsByHost.pl - Report on ClearCase views

=head1 SYNOPSIS

viewsByHost.pl [optional args]

 Options:

    -a|action       action to perform (default is list)
    -d|accessDate   restrict to views accessed since date 
    -?|help         display this usage
    -h|host         restrict to views stored on host 
    -l|logfile      name of log file to write to 
    -man            display full man page
    -o|owner        restrict to views owned by specified owner
    -uuid           uuid of specific view 
    -t|v|tag|view   view tag of specific view 
    -t|ype          view type, dynamic or snapshot 
    -verbosity      level to log (DEBUG INFO WARN ERROR FATAL)

=head1 OPTIONS

=over 8

=item B<-a|action I<action>>

Action to perform. Supported actions:

    list      - List all details of the view(s) (Default)
    listshort - List just the view tags that match the criteria 

=item B<-d|accessDate I<YYYY-MM-DD>>

Confines the listing to views that have been accessed since
the specified date in this format: YYYY-MM-DD.

=item B<-?|help>

Display this usage screen.

=item B<-h[ost] I<hostname>>

Confines the listing to views whose storage directories reside on 
host hostname.

=item B<-l[ogfile] I<path>>

Full path to the log file to send logging information to. 

=item B<-m[an]>

Display the full man page for this script.

=item B<-o[wner] I<ownerid>>

Restrict to views owned by specified owner id. Can specify a portion
of the id(s) if desired. 

=item B<-verbosity I<LEVEL>>

Log4Perl priority to log output in. Priorites are DEBUG INFO WARN 
ERROR FATAL, where DEBUG is the most verbose and FATAL is the least. 
Default is INFO.

=item B<-t|v|tag|view I<viewtag>>

Specifies a single view to be listed. The view must be registered, 
but it need not be active to be listed. The view-tag argument can 
include pattern-matching characters as described in the cleartool 
wildcards_ccase reference page. Enclose in single-quotes any 
view-tag argument that includes pattern-matching characters.

=item B<-type I<dynamic|snapshot>>

Restrict to type of view specified, either dynamic or snapshot. If
this option is omitted, both types of views will be included. 

=back

=head1 DESCRIPTION

B<viewsByHost.pl.pl> 

=cut
 
