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
our $NoOp=0;


$Result = GetOptions
    (
       "a|action=s"     => \$Action,
       "h|host=s"       => \$HostName,
       "help|?"         => \$Help,
       "l|logfile=s"    => \$LogFile,
       "man"            => \$Man,
       "noop"           => \$NoOp,
       "uuid=s"         => \$Uuid,
       "t|v|tag|view=s" => \$ViewTag,
       "verbosity=s"    => \$LogPriority
    );


sub init
{

    my $rval=1; 
    my $logMsg;

    Log::Log4perl::init_and_watch('moveView.conf', 10);
    my $logger = Log::Log4perl->get_logger('moveView.init');

    if( $LogPriority )
    {
        $LogPriority = uc $LogPriority; 
        $logger->level($LogPriority);
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

        if( $Action =~ /move/i )
        {
            if( $HostName )
            { 
                # validate dest host?
            }
            else
            {
                $logMsg="Require hostname to move view to.";
                $rval=0;
            }
        }

        if( $rval && $ViewTag && $Uuid )
        {
            $logMsg="Can't specify -uuid with either -tag or -view.";
            $logger->error($logMsg);
            $rval=0;
        }
        else
        {
            if( ! ($ViewTag || $Uuid) )
            {
                $logMsg="Must specify one of -uuid, -tag or -view";
                $logger->error($logMsg);
                $rval=0;
            }
        }

    }

    return $rval;

}

sub getViewData
{

    my $rval=1; 
    my $logger = Log::Log4perl->get_logger('moveView.getViewData');
    my $logMsg;
    my $result;
    my $lineParsed;
    my $ctCom;
    my $lsviewHashRef;
    my $viewHashRef;

    if( $LogPriority )
    {
        $logger->level($LogPriority);
    }

    my $ctCom="$Ct lsview -l -properties -full";

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
            $ctCom .= " -uuid $Uuid"; 
        }
        if( $ViewTag )
        { 
            $ctCom .= " $ViewTag"; 
        }
    }

    $lsviewHashRef = runCom($ctCom, 1);

    if( $lsviewHashRef->{"rval"} )
    {
        $logger->debug("lsview command successful. stdout follows.");
        $logger->debug($lsviewHashRef->{"stdout"});

        $viewHashRef = parseViewInfo($lsviewHashRef->{"stdout"});
        $rval=$viewHashRef;

    }
    else
    {
        $logger->debug("lsview command failed. stderr follows.");
        $logger->debug($lsviewHashRef->{"stderr"});
    }

    $rval=$viewHashRef;
    
}

sub runCom
{

    my $rval=1;
    my $com=$_[0];
    my $force=$_[1];

    my %rvalHash;
    my $pid;
    my $lineout;
    my $stdout;
    my $stderr;
    my $logMsg;

    my $logger = Log::Log4perl->get_logger('moveView.runCmd');

    if( $LogPriority )
    {
        $logger->level($LogPriority);
    }

    if( $NoOp && !$force ) 
    {
        $logMsg="NO-OP: command: $com";
        $logger->debug($logMsg);
    }
    else
    {
        $logMsg="Executing command: $com";
        $logger->debug($logMsg);

        $pid = open3(\*WRITER, \*READER, \*ERROR, $com);
        
        while( $lineout = <ERROR> ) 
        {
            #$logger->error($lineout);
            $stderr.=$lineout;
            $rval=0;
        }

        if( $rval )
        {
            while ( $lineout = <READER> )
            {
               $stdout.=$lineout;
            }
        }

        if ( waitpid( $pid, 0 ) )
        {}
        else
        {
            #$logger->error("Unable to reap the command due to: $!");
            $stderr.="Unable to reap the command due to: $!";
            $rval=0;
        }
    }


    $rvalHash{"rval"}=$rval;
    $rvalHash{"stdout"}=$stdout;
    $rvalHash{"stderr"}=$stderr;

    return \%rvalHash;

} 

sub parseViewInfo
{

    my $rval;
    my $rawViewInfo=$_[0];

    my @viewInfoArray;
    my $line;
    
    my $lineParsed;
    my %viewHash;
    my $viewTag;

    my $logger = Log::Log4perl->get_logger('moveView.parseViewInfo');

    if( $LogPriority )
    {
        $logger->level($LogPriority);
    }

    @viewInfoArray=split /\n/, $rawViewInfo;

    for $line (@viewInfoArray)
    {
        $lineParsed=0; 
        if( $line =~ /^Tag:\s+([^ ]+)(?:\s*"([^"]+)")?$/ )
        {
            $logger->debug("Parsing data for view tag: $1"); 
            $viewTag=$1; 
            $viewHash{$viewTag}{viewTagComment}=$2;
            $lineParsed=1; 
        }
        else
        {
            if( $viewTag )
            {
                if( !$lineParsed )
                {
                    if( $line =~ /^\s*Global path:\s+(.*)$/ )
                    {
                        #$logger->debug("Adding globalPath"); 
                        $viewHash{$viewTag}{globalPath}=$1;
                        $lineParsed=1; 
                    }
                }

                if( !$lineParsed )
                {
                    if( $line =~ /^\s*Server host:\s+(.*)$/ )
                    {
                        $viewHash{$viewTag}{serverHost}=$1;
                        $lineParsed=1; 
                    }
                }

                if( !$lineParsed )
                {
                    if( $line =~ /^\s*Active:\s+(.*)$/ )
                    {
                        $viewHash{$viewTag}{active}=$1;
                        $lineParsed=1; 
                    }
                }

                if( !$lineParsed )
                {
                    if( $line =~ /^\s*View uuid:\s+(.*)$/ )
                    {
                        $viewHash{$viewTag}{viewUuid}=$1;
                        $lineParsed=1; 
                    }
                }

                if( !$lineParsed )
                {
                    if( $line =~ /^\s*View on host:\s+(.*)$/ )
                    {
                        $viewHash{$viewTag}{viewHost}=$1;
                        $lineParsed=1; 
                    }
                }

                if( !$lineParsed )
                {
                    #dev.sabre.com/
                    if( $line =~ /^\s*View owner:\s+((?:dev\.sabre\.com\/)?(.*))$/ )
                    {
                        $viewHash{$viewTag}{viewOwner}=$1;
                        $viewHash{$viewTag}{viewOwnerId}=$2;
                        $lineParsed=1; 
                    }
                }

                if( !$lineParsed )
                {
                    if( $line =~ /^Created\s+([^ ]+)\s+by\s+(.*)$/ )
                    {
                        $viewHash{$viewTag}{createdDate}=$1;
                        $viewHash{$viewTag}{createdUser}=$2;
                        $lineParsed=1; 
                    }
                }

                if( !$lineParsed )
                {
                    if( $line =~ /^Last modified\s+([^ ]+)\s+by\s+(.*)$/ )
                    {
                        $viewHash{$viewTag}{lastModifiedDate}=$1;
                        $viewHash{$viewTag}{lastModifiedUser}=$2;
                        $lineParsed=1; 
                    }
                }

                if( !$lineParsed )
                {
                    if( $line =~ /^Last accessed\s+([^ ]+)\s+by\s+(.*)$/ )
                    {
                        $viewHash{$viewTag}{lastAccessedDate}=$1;
                        $viewHash{$viewTag}{lastAccessedUser}=$2;
                        $lineParsed=1; 
                    }
                }

                if( !$lineParsed )
                {
                    if( $line =~ /^Last read of private data\s+([^ ]+)\s+by\s+(.*)$/ )
                    {
                        $viewHash{$viewTag}{lastReadOfPrivateDataDate}=$1;
                        $viewHash{$viewTag}{lastReadOfPrivateDataUser}=$2;
                        $lineParsed=1; 
                    }
                }

                if( !$lineParsed )
                {
                    if( $line =~ /^Last config spec update\s+([^ ]+)\s+by\s+(.*)$/ )
                    {
                        $viewHash{$viewTag}{lastConfigSpecUpdateDate}=$1;
                        $viewHash{$viewTag}{lastConfigSpecUpdateUser}=$2;
                        $lineParsed=1; 
                    }
                }

                if( !$lineParsed )
                {
                    if( $line =~ /^Last view private object update\s+([^ ]+)\s+by\s+(.*)$/ )
                    {
                        $viewHash{$viewTag}{lastViewPrivateObjectUpdateDate}=$1;
                        $viewHash{$viewTag}{lastViewPrivateObjectUpdateUser}=$2;
                        $lineParsed=1; 
                    }
                }

                if( !$lineParsed )
                {
                    if( $line =~ /^Properties:\s+(.*)$/ )
                    {
                        
                        $viewHash{$viewTag}{properties}=[ split / /, $1 ];
                        $lineParsed=1; 
                    }
                }

                if( !$lineParsed )
                {
                    if( $line =~ /^\s*Owner:\s+([^ ]+)\s+:\s+([^ ]+)\s+\((.*)\)$/ )
                    {
                        $viewHash{$viewTag}{owner}=$1;
                        $viewHash{$viewTag}{ownerPermissions}=$2;
                        $viewHash{$viewTag}{ownerPermissionsScope}=$3;
                        $lineParsed=1; 
                    }
                }

                if( !$lineParsed )
                {
                    if( $line =~ /^\s*Group:\s+([^ ]+)\s+:\s+([^ ]+)\s+\((.*)\)$/ )
                    {
                        $viewHash{$viewTag}{group}=$1;
                        $viewHash{$viewTag}{groupPermissions}=$2;
                        $viewHash{$viewTag}{groupPermissionsScope}=$3;
                        $lineParsed=1; 
                    }
                }

            }
            else
            {
                $logger->debug("Not within a view so skipping this line: $line"); 
            }
        }


    } # foreach

    return \%viewHash;

}

sub listView
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

    my $logger = Log::Log4perl->get_logger('moveView.listView');
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

sub endView
{

    my $rval=1;
    my $vHashRef=$_[0];
    my $logger = Log::Log4perl->get_logger('moveView.endView');
    my $logMsg;
    my $viewTag;
    my $ctCom;
    my $ctHashRef; 

    my %rvalHash;

    if( $LogPriority )
    {
        $logger->level($LogPriority);
    }

    for $viewTag (sort keys %{ $vHashRef } )
    {    
        if ( $vHashRef->{$viewTag}{active} =~ /yes/i )
        {
            $logMsg="View is active so running 'endview' on it now.";
            $logger->info($logMsg); 

            $ctCom="$Ct endview $viewTag"; 

            $ctHashRef = runCom($ctCom, 0);

            if( $ctHashRef->{"rval"} )
            {
                $logger->info("endview command successful.");
                $vHashRef = getViewData();
                #$logger->debug($ctHashRef->{"stdout"});
            }
            else
            {
                $logger->error("lsview command failed. stderr follows.");
                $logger->error($ctHashRef->{"stderr"});
                $rval=0;
            }

        }
        else
        {
            $logMsg="View is already inactive -- ";
            $logMsg.=" no need to 'endview' it.";
            $logger->info($logMsg); 
        }
    }

    $rvalHash{"rval"}=$rval;
    $rvalHash{"viewHashRef"}=$vHashRef;

    return \%rvalHash;

}

sub reformatView
{

    my $rval=1;
    my $vHashRef=$_[0];
    my $logger = Log::Log4perl->get_logger('moveView.reformatView');
    my $logMsg;
    my $viewTag;
    my $ctCom;
    my $ctHashRef; 

    my %rvalHash;

    if( $LogPriority )
    {
        $logger->level($LogPriority);
    }

    for $viewTag (sort keys %{ $vHashRef } )
    {    

        $ctCom="$Ct reformatview -dump -tag $viewTag"; 

        $ctHashRef = runCom($ctCom, 0);

        if( $ctHashRef->{"rval"} )
        {
            $logger->info("reformatview command successful.");
            $vHashRef = getViewData();
            #$logger->debug($ctHashRef->{"stdout"});
        }
        else
        {
            $logger->error("reformatview command failed. stderr follows.");
            $logger->error($ctHashRef->{"stderr"});
            $rval=0;
        }
    }

    $rvalHash{"rval"}=$rval;
    $rvalHash{"viewHashRef"}=$vHashRef;

    return \%rvalHash;

}

sub moveView
{

    my $rval;
    my $vHashRef;
    my $viewTag;
    my $logger = Log::Log4perl->get_logger('moveView.moveView');
    my $logMsg;

    my $stepHashRef;

    if( $LogPriority )
    {
        $logger->level($LogPriority);
    }

    $vHashRef = getViewData();
    if ( $vHashRef )
    {
        $logMsg="View is healthy. Listing info on it pre-move.";
        $logger->info($logMsg); 
        listView('long', $vHashRef);

        if( $rval )
        {
            $stepHashRef = endView($vHashRef); 
            $rval=$stepHashRef->{"rval"};
        }

        if( $rval )
        {
            # reload the hash with info on the view
            $vHashRef = $stepHashRef->{viewHashRef}; 
            listView('long', $vHashRef);
        }

    }
    else
    {
        $logMsg="Unable to get info on view so not attempting to move it.";
        $logger->error($logMsg); 
    }

    return $rval;

}

if( init )
{
    if( moveView() )
    {
    }

}
